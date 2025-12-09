import enum
import re
from contextlib import suppress
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from faststream.rabbit import RabbitQueue
import asyncio

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
    CartNotFoundError,
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
    if not cache_cart:
        logger.error(f'calculate_cart: cart not found in cache for uuid={uuid}')
        raise CartNotFoundError
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
        logger.debug(
            'calculate_cart: após calculate_subtotal, '
            f'subtotal={cart.subtotal}, total={cart.total}',
        )
    cache.set(
        str(cart.uuid),
        cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    logger.debug(
        'calculate_cart: carrinho salvo no cache '
        f'com subtotal={cart.subtotal}, total={cart.total}',
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
            freight.price = Decimal('0.01')
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
    logger.debug(
        'add_payment_information: '
        f'uuid={uuid}, payment_method={payment_method}, '
        f'payment_type={type(payment)}',
    )
    user = bootstrap.user.get_user(token)
    cache_cart = bootstrap.cache.get(uuid)
    cache_cart = CartShipping.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise InvalidCartUUIDError
    if not payment.payment_gateway:
        logger.error(f'payment_gateway is missing: {payment}')
        raise PaymentNotFoundError

    logger.debug(f'Payment gateway: {payment.payment_gateway}, calling payment_process')
    _payment = PaymentGatewayProcess[payment.payment_gateway].value
    cart = await _payment.payment_process(
        payment_method,
        user=user,
        cache_cart=cache_cart,
        payment=payment,
        bootstrap=bootstrap,
    )
    logger.debug(
        'Saving cart to cache after payment: '
        f'payment_method={cart.payment_method}, '
        f'gateway_provider={cart.gateway_provider}, uuid={cart.uuid}',
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
    if not cart:
        logger.error(f'Cart não encontrado no cache: uuid={uuid}')
        raise CartNotFoundError
    logger.debug(
        'Preview: cart do cache (primeiros 200 chars): '
        f'{str(cart)[:200] if cart else None}',
    )
    try:
        cache_cart = CartPayment.model_validate_json(cart)
        logger.debug(
            'Preview: CartPayment validado, '
            f'payment_method={cache_cart.payment_method}, '
            f'gateway_provider={cache_cart.gateway_provider}',
        )
    except (TypeError, ValueError) as e:
        logger.error(f'Erro ao validar cart do cache como CartPayment: {e}')
        try:
            _ = CartShipping.model_validate_json(cart)
            logger.warning(
                'Cart no cache é CartShipping, não CartPayment. '
                f'UUID={uuid}. Pagamento ainda não adicionado.',
            )
        except (TypeError, ValueError) as e2:
            logger.error(f'Erro ao validar como CartShipping: {e2}')
            raise CartNotFoundError from e
        msg = 'Payment method not added yet'
        raise CartNotFoundError(msg) from None
    if cache_cart.gateway_provider == PaymentGatewayAvailable.STRIPE.name:
        try:
            customer_stripe = await bootstrap.cart_uow.get_customer(
                user.user_id,
                payment_gateway=PaymentGatewayAvailable.STRIPE.name,
                bootstrap=bootstrap,
            )
            if customer_stripe and cache_cart.payment_method_id:
                payment_intent = bootstrap.payment.create_payment_intent(
                    amount=cache_cart.subtotal,
                    currency='brl',
                    customer_id=customer_stripe.customer_uuid,
                    payment_method=cache_cart.payment_method_id,
                    installments=cache_cart.installments,
                )
                cache_cart.payment_intent = payment_intent['id']
            else:
                logger.warning(
                    'Customer/payment_method_id missing: cust=%s, method=%s',
                    customer_stripe,
                    cache_cart.payment_method_id,
                )
        except Exception as e:  # noqa: BLE001
            logger.error(f'Erro ao criar payment intent: {e}')
    bootstrap.cache.set(
        str(cache_cart.uuid),
        cache_cart.model_dump_json(),
        ex=DEFAULT_CART_EXPIRE,
    )
    return cache_cart


async def checkout(  # noqa: C901, PLR0912, PLR0915
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
    now = datetime.now(timezone.utc)
    await cart_repository.upsert_checkout_job(
        cart_uuid=uuid,
        payment_gateway=cache_cart.gateway_provider,
        payment_method=cache_cart.payment_method,
        payload=cache_cart.model_dump(),
        status='pending',
        attempts=0,
        next_run_at=now,
        last_error=None,
        order_id=None,
        gateway_payment_id=None,
        transaction=bootstrap.db,
    )
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
    logger.info('Finish Checkout task publish')
    direct_order_id = None
    direct_gateway_payment_id = None
    direct_qr_code = None
    direct_qr_code_base64 = None
    if isinstance(checkout_task, dict):
        _order = checkout_task.get('order_id')
        _gateway_payment = checkout_task.get('gateway_payment_id')
        direct_qr_code = checkout_task.get('qr_code')
        direct_qr_code_base64 = checkout_task.get('qr_code_base64')
        if isinstance(_order, list):
            direct_order_id = str(_order.pop()) if _order else None
        elif _order:
            direct_order_id = str(_order)
        if isinstance(_gateway_payment, list):
            if _gateway_payment:
                direct_gateway_payment_id = str(_gateway_payment.pop())
        elif _gateway_payment is not None:
            direct_gateway_payment_id = str(_gateway_payment)
        if direct_order_id:
            await cart_repository.upsert_checkout_job(
                cart_uuid=uuid,
                payment_gateway=cache_cart.gateway_provider,
                payment_method=cache_cart.payment_method,
                payload=cache_cart.model_dump(),
                status='succeeded',
                attempts=0,
                next_run_at=None,
                last_run_at=now,
                last_error=None,
                order_id=direct_order_id,
                gateway_payment_id=direct_gateway_payment_id,
                transaction=bootstrap.db,
            )
            return CreateCheckoutResponse(
                message=str(checkout_task.get('message', 'processed')),
                status='processing',
                order_id=direct_order_id,
                gateway_payment_id=direct_gateway_payment_id or '',
                qr_code=direct_qr_code,
                qr_code_base64=direct_qr_code_base64,
                job_status='succeeded',
                next_retry_at=None,
            )
        if not direct_order_id:
            logger.warning(
                'checkout_task sem order_id (gateway=%s, cart_uuid=%s); '
                'marcando job como failed e levantando erro.',
                cache_cart.gateway_provider,
                uuid,
            )
            await cart_repository.upsert_checkout_job(
                cart_uuid=uuid,
                payment_gateway=cache_cart.gateway_provider,
                payment_method=cache_cart.payment_method,
                payload=cache_cart.model_dump(),
                status='failed',
                attempts=0,
                next_run_at=None,
                last_run_at=now,
                last_error='order_id missing from checkout task',
                order_id=None,
                gateway_payment_id=(
                    direct_gateway_payment_id if direct_gateway_payment_id else None
                ),
                transaction=bootstrap.db,
            )
            raise CheckoutProcessingError
    job = None
    for attempt in range(10):
        await asyncio.sleep(0.3)
        job = await cart_repository.get_checkout_job(
            cart_uuid=uuid,
            transaction=bootstrap.db,
        )
        if job:
            logger.info(
                'Job encontrado após %s tentativas: status=%s, order_id=%s',
                attempt + 1,
                job.status,
                job.order_id,
            )
            if job.status == 'succeeded' and job.order_id:
                break
            if job.status == 'failed' and job.next_run_at is None:
                logger.warning(f'Job falhou permanentemente: {job.last_error}')
                raise CheckoutProcessingError
    if not job:
        logger.warning(
            'Job não encontrado após publish (gateway=%s, cart_uuid=%s)',
            cache_cart.gateway_provider,
            uuid,
        )
        return CreateCheckoutResponse(
            message='processing',
            status='processing',
            order_id='',
            gateway_payment_id='',
            qr_code=_qr_code,
            qr_code_base64=_qr_code_base64,
            job_status='pending',
            next_retry_at=None,
        )
    job_status = job.status if job else 'processing'
    next_retry_at = job.next_run_at if job else None
    order_id = job.order_id if job else None
    gateway_payment_id = job.gateway_payment_id if job else None
    _qr_code = None
    _qr_code_base64 = None
    if cache_cart.payment_method == PaymentMethod.PIX.value:
        _qr_code = cache_cart.pix_qr_code
        _qr_code_base64 = cache_cart.pix_qr_code_base64
    if job_status == 'succeeded' and order_id:
        return CreateCheckoutResponse(
            message='processed',
            status='processing',
            order_id=str(order_id),
            gateway_payment_id=str(gateway_payment_id) if gateway_payment_id else '',
            qr_code=_qr_code,
            qr_code_base64=_qr_code_base64,
            job_status=job_status,
            next_retry_at=next_retry_at,
        )
    if job_status == 'failed':
        logger.warning(
            'Job falhou (gateway=%s, cart_uuid=%s, error=%s)',
            cache_cart.gateway_provider,
            uuid,
            job.last_error,
        )
        raise CheckoutProcessingError
    return CreateCheckoutResponse(
        message='processing',
        status='processing',
        order_id=str(order_id) if order_id else '',
        gateway_payment_id=str(gateway_payment_id) if gateway_payment_id else '',
        qr_code=_qr_code,
        qr_code_base64=_qr_code_base64,
        job_status=job_status,
        next_retry_at=next_retry_at,
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
