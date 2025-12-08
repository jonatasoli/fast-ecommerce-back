import enum
import re
from contextlib import suppress
from decimal import Decimal

from fastapi import HTTPException
from faststream.rabbit import RabbitQueue
from loguru import logger
from pydantic import ValidationError

from app.campaign import repository as campaign_repository
from app.cart import repository as cart_repository
from app.entities.address import CreateAddress
from app.entities.cart import (
    CartBase,
    CartPayment,
    CartShipping,
    CartUser,
    CheckoutProcessingError,
    CreateCheckoutResponse,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
    InvalidCartUUIDError,
    generate_empty_cart,
    generate_new_cart,
    validate_cache_cart,
)
from app.entities.coupon import (
    CouponDontMatchWithUserError,
    CouponInDB,
    CouponNotFoundError,
)
from app.entities.payment import CustomerNotFoundError, PaymentNotFoundError
from app.entities.product import ProductCart, ProductSoldOutError
from app.entities.user import UserData, UserDBGet
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod
from app.infra.crm.rd_station import send_abandonated_cart_to_crm
from app.infra.redis import RedisCache
from app.payment import (
    payment_process_cielo,
    payment_process_mercado_pago,
    payment_process_stripe,
)


class UserAddressNotFoundError(Exception):
    """User address not found."""


class PaymentGatewayProcess(enum.Enum):
    MERCADOPAGO = payment_process_mercado_pago
    STRIPE = payment_process_stripe
    CIELO = payment_process_cielo


DEFAULT_CART_EXPIRE = 432_000
DEFAULT_ABANDONED_CART = 172800


def raise_checkout_error():
    """Raise checkout errors."""
    raise CheckoutProcessingError


def create_or_get_cart(
    uuid: str | None,
    token: str | None,
    bootstrap: Command,
) -> CartBase:
    """Must create or get cart and return cart."""
    cart = None
    cache = bootstrap.cache
    if token:
        cart = cache.get(token)
    elif uuid:
        cart = cache.get(uuid)
    else:
        cart = generate_empty_cart()
        cache.set(
            str(cart.uuid),
            cart.model_dump_json(),
            ex=DEFAULT_CART_EXPIRE,
        )
    return cart


async def add_product_to_cart(
    cart_uuid: str | None,
    product: ProductCart,
    bootstrap: Command,
    db,
) -> CartBase:
    """Must add product to new cart and return cart."""
    cache = bootstrap.cache
    async with db().begin() as transaction:
        product_db = await cart_repository.get_product_by_id(
            product.product_id,
            transaction=transaction,
        )
    logger.info(f'product_db: {product_db}')
    cart = None
    if cart_uuid:
        cart = cache.get(cart_uuid)
    if not cart:
        cart = generate_new_cart(
            product=product_db,
            price=product_db.price,
            quantity=product.quantity,
            available_quantity=product_db.quantity,
        )
    else:
        cart = cache.get(cart_uuid)
        cart = CartBase.model_validate_json(cart)
        cart.add_product(
            product_id=product.product_id,
            quantity=product.quantity,
            name=product_db.name,
            price=product_db.price,
            image_path=product_db.image_path,
            available_quantity=product_db.quantity,
        )
    cache.set(str(cart.uuid), cart.model_dump_json(), ex=DEFAULT_CART_EXPIRE)
    return cart


async def calculate_cart(
    uuid: str,
    cart: CartBase,
    bootstrap: Command,
    session,
) -> CartBase:
    """Must calculate cart and return cart."""
    cache = bootstrap.cache
    cache_cart = cache.get(uuid)
    logger.info(cache_cart)
    cache_cart = CartBase.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise HTTPException(
            status_code=400,
            detail='Cart uuid is not the same as the cache uuid',
        )
    product_ids: list[int] = [item.product_id for item in cart.cart_items]
    async with session().begin() as transaction:
        products_inventory = await cart_repository.get_products_quantity(
            product_ids,
            transaction=transaction,
        )
    cart = consistency_inventory(
        cart,
        products_inventory=products_inventory,
    )
    if cart:
        cache.set(
            str(cart.uuid),
            cart.model_dump_json(),
            ex=DEFAULT_CART_EXPIRE,
        )

    cart.get_products_price_and_discounts(products_inventory)
    if cart.coupon:
        async with session().begin() as transaction:
            coupon = await cart_repository.get_coupon_by_code(
                cart.coupon,
                transaction=transaction,
            )
    if cart.coupon and not coupon:
        raise HTTPException(
            status_code=400,
            detail='Coupon not found',
        )
    cart = await calculate_freight(
        cart=cart,
        products_db=products_inventory,
        bootstrap=bootstrap,
        session=session,
    )
    if cart.cart_items:
        cart.calculate_subtotal(
            coupon=coupon if cart.coupon and coupon else None,
        )
    cache.set(
        str(cart.uuid),
        cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    return cart


async def calculate_freight(
    cart: CartBase,
    products_db,
    bootstrap: Command,
    session,
) -> CartBase:
    """Calculate Freight."""
    async with session().begin() as transaction:
        logger.debug('Search campaign')
        campaign = await campaign_repository.get_campaign(
            free_shipping=True,
            transaction=transaction,
        )
    if cart.zipcode:
        zipcode = cart.zipcode
        no_spaces = zipcode.replace(' ', '')
        no_special_chars = re.sub(r'[^a-zA-Z0-9]', '', no_spaces)
        cart.zipcode = no_special_chars
        freight_package = bootstrap.freight.calculate_volume_weight(
            products=products_db,
        )
        if not cart.freight_product_code:
            raise HTTPException(
                status_code=400,
                detail='Freight product code not found',
            )
        freight = bootstrap.freight.get_freight(
            cart.freight_product_code,
            freight_package=freight_package,
            zipcode=cart.zipcode,
        )
        logger.debug(f'Campaign: {campaign}')
        if campaign and cart.subtotal > campaign.min_purchase_value:
            logger.debug('Campaign')
            freight.price = Decimal(0.01)  # noqa: RUF032
        cart.freight = freight
    return cart


def consistency_inventory(
    cart: CartBase,
    *,
    products_inventory: list,
) -> CartBase:
    """Check if products there are in invetory."""
    if len(cart.cart_items) != len(products_inventory):
        raise ProductSoldOutError
    for product in products_inventory:
        for cart_item in cart.cart_items:
            if cart_item.product_id == product.product_id:
                if cart_item.quantity > product.quantity:
                    raise ProductSoldOutError
                cart_item.available_quantity = max(product.quantity, 0)

    return cart


async def add_user_to_cart(
    uuid: str,
    cart: CartBase,
    token: str,
    bootstrap: Command,
) -> CartUser:
    """Must validate token user if is valid add user id in cart."""
    user = bootstrap.user.get_user(token)
    customer_stripe = None
    customer_mercadopago = None
    with suppress(CustomerNotFoundError):
        customer_stripe = await bootstrap.cart_uow.get_customer(
            user.user_id,
            payment_gateway=PaymentGatewayAvailable.STRIPE.name,
            bootstrap=bootstrap,
        )
        customer_mercadopago = await bootstrap.cart_uow.get_customer(
            user.user_id,
            payment_gateway=PaymentGatewayAvailable.MERCADOPAGO.name,
            bootstrap=bootstrap,
        )
    if not customer_stripe or not customer_mercadopago:
        await bootstrap.message.broker.publish(
            {'user_id': user.user_id, 'user_email': user.email},
            queue=RabbitQueue('create_customer'),
        )
    user_data = UserData.model_validate(user)
    logger.debug(user_data)
    cart_user = CartUser(**cart.model_dump(), user_data=user_data)
    if cart_user.coupon and cart_user.coupon != 'null':
        logger.debug('Coupon')
        logger.debug(cart_user.coupon)
        async with bootstrap.db() as session:
            coupon = await bootstrap.cart_repository.get_coupon_by_code(
                cart_user.coupon,
                transaction=session.begin(),
            )
        match coupon:
            case None:
                raise CouponNotFoundError
            case _ if coupon.user_id and coupon.user_id != user_data.user_id:
                raise CouponDontMatchWithUserError
    cache = bootstrap.cache
    logger.debug('Antes do get UUID')
    cache.get(uuid)
    logger.debug(cache)
    cache.set(
        str(cart.uuid),
        cart_user.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    logger.debug('set cache')
    return cart_user


async def add_address_to_cart(
    uuid: str,
    cart: CartUser,
    address: CreateAddress,
    token: str,
    bootstrap: Command,
) -> CartShipping:
    """Must add addresss information to shipping and payment."""
    user = bootstrap.user.get_user(token)
    cache_cart = bootstrap.cache.get(uuid)
    cache_cart = CartUser.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise HTTPException(
            status_code=400,
            detail='Cart uuid is not the same as the cache uuid',
        )
    address_id = address.user_address.address_id
    user_id = user.user_id
    user_address_id = None
    if user_id and address_id:
        user_address_id = await bootstrap.uow.get_address_by_id(
            address_id,
            user_id,
        )
    if not user_address_id:
        user_address_id = await bootstrap.uow.create_address(
            address.user_address,
            cache_cart.user_data,
        )
    shipping_address_id = None
    if not address.shipping_is_payment:
        shipping_address_id = await bootstrap.uow.create_address(
            address.shipping_address,
            cache_cart.user_data,
        )
    if not user_address_id:
        raise UserAddressNotFoundError
    cart = CartShipping(
        **cache_cart.model_dump(),
        shipping_is_payment=address.shipping_is_payment,
        user_address_id=user_address_id,
        shipping_address_id=shipping_address_id,
    )
    bootstrap.cache.set(
        str(cart.uuid),
        cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    return cart


async def add_payment_information(  # noqa: PLR0913
    uuid: str,
    payment_method: str,
    cart: CartShipping,
    payment: CreateCreditCardPaymentMethod
    | CreatePixPaymentMethod
    | CreateCreditCardTokenPaymentMethod,
    token: str,
    bootstrap: Command,
) -> CartPayment:
    """Must add payment information and create token in payment gateway."""
    user = bootstrap.user.get_user(token)
    cache_cart = bootstrap.cache.get(uuid)
    cache_cart = CartShipping.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise InvalidCartUUIDError
    if not payment.payment_gateway:
        raise PaymentNotFoundError

    _payment = PaymentGatewayProcess[payment.payment_gateway].value
    cart = await _payment.payment_process(
        payment_method,
        user=user,
        cache_cart=cache_cart,
        payment=payment,
        bootstrap=bootstrap,
    )
    bootstrap.cache.set(
        str(cart.uuid),
        cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    return cart


async def preview(
    uuid: str,
    token: str,
    bootstrap: Command,
) -> CartPayment:
    """Must get address id and payment token to show in cart."""
    user = bootstrap.user.get_user(token)
    cart = bootstrap.cache.get(uuid)
    cache_cart = CartPayment.model_validate_json(cart)
    if cache_cart.gateway_provider == PaymentGatewayAvailable.STRIPE.name:
        customer_stripe = await bootstrap.cart_uow.get_customer(
            user.user_id,
            payment_gateway=PaymentGatewayAvailable.STRIPE.name,
            bootstrap=bootstrap,
        )
        payment_intent = bootstrap.payment.create_payment_intent(
            amount=cache_cart.subtotal,
            currency='brl',
            customer_id=customer_stripe.customer_uuid,
            payment_method=cache_cart.payment_method_id,
            installments=cache_cart.installments,
        )
        cache_cart.payment_intent = payment_intent['id']
    bootstrap.cache.set(
        str(cache_cart.uuid),
        cache_cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    return cache_cart


async def checkout(
    uuid: str,
    cart: CartPayment,
    token: str,
    bootstrap: Command,
) -> CreateCheckoutResponse:
    """Process payment to specific cart."""
    _ = cart
    user = bootstrap.user.get_user(token)
    cache_cart = bootstrap.cache.get(uuid)
    validate_cache_cart(cache_cart)
    cache_cart = CartPayment.model_validate_json(cache_cart)
    _qr_code = None
    _qr_code_base64 = None

    if cache_cart.payment_method not in {
        PaymentMethod.CREDIT_CARD.value,
        PaymentMethod.PIX.value,
    }:
        raise HTTPException(
            status_code=400,
            detail='Payment method not found',
        )

    logger.info(f'{uuid}, {cache_cart.payment_intent} ')
    user = UserDBGet.model_validate(user)
    logger.info('Service Checkout')
    logger.info(f'{uuid}')
    logger.info(f'{cache_cart.gateway_provider}')
    logger.info(f'{cache_cart.payment_method}')
    logger.info(f'{user}')
    checkout_task = await bootstrap.message.broker.publish(
        {
            'cart_uuid': uuid,
            'payment_gateway': cache_cart.gateway_provider,
            'payment_method': cache_cart.payment_method,
            'user': user,
        },
        queue=RabbitQueue('checkout'),
    )
    logger.info('Finish Checkout task')
    order_id = None
    _gateway_payment_id = None
    if not isinstance(checkout_task, dict):
        checkout_task = {}
    else:
        _order_id = checkout_task.get('order_id')
        _gateway_payment_id = checkout_task.get('gateway_payment_id')
        _qr_code = checkout_task.get('qr_code')
        _qr_code_base64 = checkout_task.get('qr_code_base64')
        if isinstance(_order_id, list):
            order_id = str(_order_id.pop())
        if isinstance(_gateway_payment_id, list):
            _gateway_payment_id = str(_gateway_payment_id.pop())
        if isinstance(_gateway_payment_id, int):
            _gateway_payment_id = str(_gateway_payment_id)
    if not order_id:
        raise_checkout_error()
    return CreateCheckoutResponse(
        message=str(checkout_task.get('message')),
        status='processing',
        order_id=order_id,
        gateway_payment_id=_gateway_payment_id if _gateway_payment_id else '',
        qr_code=_qr_code,
        qr_code_base64=_qr_code_base64,
    )


async def get_coupon(code: str, bootstrap: Command) -> CouponInDB:
    """Must get coupon and return cart."""
    async with bootstrap.db().begin() as transaction:
        coupon = await bootstrap.cart_uow.get_coupon_by_code(
            code,
            transaction=transaction,
        )
        logger.debug(f'Coupon CODE {coupon}')
        if not coupon:
            raise HTTPException(
                status_code=400,
                detail='Coupon not found',
            )
    return coupon


async def get_cart_and_send_to_crm(_cache=RedisCache) -> None:
    """Get all keys and set user data to CRM."""
    cache = _cache()
    cache_cart = None
    keys = cache.get_all_keys_with_lower_ttl(ttl_target=DEFAULT_ABANDONED_CART)
    for k in keys:
        cart = cache.redis.get(k)
        try:
            logger.info('Start sending to CRM')
            cache_cart = CartUser.model_validate_json(cart)
            logger.info(cache_cart.user_data)
            await send_abandonated_cart_to_crm(cache_cart.user_data)
            cache.redis.delete(k)

        except ValidationError:
            logger.error(f'Cart not valid to send for CRM. {k}')
            cache.redis.delete(k)
            cache_cart = None
