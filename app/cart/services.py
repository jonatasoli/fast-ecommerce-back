# ruff: noqa: PLR1714
from contextlib import suppress
import re

from fastapi import HTTPException
from loguru import logger
from faststream.rabbit import RabbitQueue
from pydantic import ValidationError


from app.entities.address import CreateAddress
from app.entities.cart import (
    CartBase,
    CartUser,
    CartShipping,
    CartPayment,
    CheckoutProcessingError,
    CreateCheckoutResponse,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
    generate_empty_cart,
    generate_new_cart,
    validate_cache_cart,
)
from app.entities.coupon import (
    CouponDontMatchWithUserError,
    CouponNotFoundError,
    CouponResponse,
)
from app.entities.payment import CustomerNotFoundError
from app.entities.product import ProductCart, ProductSoldOutError
from app.entities.user import UserDBGet, UserData
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod
from app.infra.crm.rd_station import send_abandonated_cart_to_crm
from app.infra.redis import RedisCache


class UserAddressNotFoundError(Exception):
    """User address not found."""


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
) -> CartBase:
    """Must add product to new cart and return cart."""
    cache = bootstrap.cache
    async with bootstrap.db() as session:
        product_db = await bootstrap.cart_repository.get_product_by_id(
            product.product_id,
            transaction=session,
        )
    logger.info(f'product_db: {product_db}')
    cart = None
    if cart_uuid:
        cart = cache.get(cart_uuid)
    if None or not cart:
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
    async with bootstrap.db() as db:
        products_inventory = (
            await bootstrap.cart_repository.get_products_quantity(
                product_ids,
                transaction=db.begin(),
            )
        )
    cart = consistency_inventory(
        cart,
        products_inventory=products_inventory,
    )
    if cart:
        cache.set(
            str(cart.uuid),
            cache_cart.model_dump_json(),
            ex=DEFAULT_CART_EXPIRE,
        )

    cart.get_products_price_and_discounts(products_inventory)
    if cart.coupon:
        async with bootstrap.db() as session:
            coupon = await bootstrap.cart_repository.get_coupon_by_code(
                cart.coupon,
                transaction=session.begin(),
            )
    if cart.coupon and not coupon:
        raise HTTPException(
            status_code=400,
            detail='Coupon not found',
        )
    cart = calculate_freight(
        cart=cart,
        products_db=products_inventory,
        bootstrap=bootstrap,
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


def calculate_freight(
    cart: CartBase,
    products_db: ProductCart,
    bootstrap: Command,
) -> CartBase:
    """Calculate Freight."""
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
    cart_user = CartUser(**cart.model_dump(), user_data=user_data)
    if cart_user.coupon:
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
    cache.get(uuid)
    cache.set(
        str(cart.uuid),
        cart_user.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
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
        **cart.model_dump(),
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
        raise HTTPException(
            status_code=400,
            detail='Cart uuid is not the same as the cache uuid',
        )
    if not payment.payment_gateway:
        raise HTTPException(
            status_code=400,
            detail='Payment not defined',
        )
    customer = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=payment.payment_gateway,
        bootstrap=bootstrap,
    )
    if payment_method == PaymentMethod.PIX.value and isinstance(
        payment,
        CreatePixPaymentMethod,
    ):
        description = " ".join(
            item.name for item in cache_cart.cart_items if item.name
        )

        payment_gateway = 'mercadopago_gateway'
        _payment = getattr(bootstrap.payment, payment_gateway).create_pix(
            customer.customer_uuid,
            customer_email=user.email,
            description=description,
            amount=int(cache_cart.subtotal),
        )
        qr_code = _payment.point_of_interaction.transaction_data.qr_code
        qr_code_base64 = (
            _payment.point_of_interaction.transaction_data.qr_code_base64
        )
        payment_id = _payment.id
        cart = CartPayment(
            **cache_cart.model_dump(),
            payment_method=payment_method,
            gateway_provider=payment.payment_gateway,
            customer_id=customer.customer_uuid,
            pix_qr_code=qr_code,
            pix_qr_code_base64=qr_code_base64,
            pix_payment_id=payment_id,
            payment_method_id=str(payment_id),
        )
        bootstrap.cache.set(
            str(cart.uuid),
            cart.model_dump_json(),
            ex=DEFAULT_CART_EXPIRE,
        )
        return cart
    if not isinstance(
        payment,
        CreateCreditCardPaymentMethod | CreateCreditCardTokenPaymentMethod,
    ):
        raise HTTPException(
            status_code=400,
            detail='Payment method not found',
        )
    installments = payment.installments
    payment_method_id = bootstrap.payment.attach_customer_in_payment_method(
        payment_gateway=payment.payment_gateway,
        card_token=payment.card_token,
        card_issuer=payment.card_issuer,
        card_brand=payment.card_brand,
        customer_uuid=customer.customer_uuid,
        email=user.email,
    )
    if not payment_method_id:
        raise HTTPException(
            status_code=400,
            detail='Payment method id not found',
        )
    cart = CartPayment(
        **cache_cart.model_dump(),
        payment_method=PaymentMethod.CREDIT_CARD.value,
        payment_method_id=payment_method_id,
        gateway_provider=payment.payment_gateway,
        card_token=payment.card_token,
        customer_id=customer.customer_uuid,
        installments=installments,
    )
    _payment_installment_fee = await bootstrap.cart_uow.get_installment_fee(
        bootstrap=bootstrap,
    )
    if cart.installments >= _payment_installment_fee.min_installment_with_fee:
        cart.calculate_fee(_payment_installment_fee.fee)
    bootstrap.cache.set(
        str(cart.uuid),
        cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    await bootstrap.uow.update_payment_method_to_user(
        user.user_id,
        payment_method_id,
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
        payment_intent = bootstrap.payment.create_payment_intent(
            amount=cache_cart.subtotal,
            currency='brl',
            customer_id=user.customer_uuid,
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

    if (
        cache_cart.payment_method != PaymentMethod.CREDIT_CARD.value
        and cache_cart.payment_method != PaymentMethod.PIX.value
    ):
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
        rpc=True,
    )
    logger.info('Finish Checkout task')
    order_id = None
    _gateway_payment_id = None
    if not isinstance(checkout_task, dict):
        checkout_task = {}
    else:
        _order_id = checkout_task.get('order_id', None)
        _gateway_payment_id = checkout_task.get('gateway_payment_id', None)
        _qr_code = checkout_task.get('qr_code', None)
        _qr_code_base64 = checkout_task.get('qr_code_base64', None)
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


async def get_coupon(code: str, bootstrap: Command) -> CouponResponse:
    """Must get coupon and return cart."""
    async with bootstrap.db().begin() as transaction:
        coupon = await bootstrap.cart_uow.get_coupon_by_code(
            code,
            transaction=transaction,
        )
        if not coupon:
            raise HTTPException(
                status_code=400,
                detail='Coupon not found',
            )
    return coupon



async def get_cart_and_send_to_crm(_cache = RedisCache) -> None:
    """Get all keys and set user data to CRM."""
    cache = _cache()
    cache_cart = None
    keys = cache.get_all_keys_with_lower_ttl(ttl_target=DEFAULT_ABANDONED_CART)
    for k in keys:
        cart = cache.redis.get(k)
        try:
            logger.info("Start sending to CRM")
            cache_cart = CartUser.model_validate_json(cart)
            logger.info(cache_cart.user_data)
            await send_abandonated_cart_to_crm(cache_cart.user_data)
            cache.redis.delete(k)

        except ValidationError:
            logger.error(f"Cart not valid to send for CRM. {k}")
            cache.redis.delete(k)
            cache_cart = None
