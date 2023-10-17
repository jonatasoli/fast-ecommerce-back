from fastapi import HTTPException
from loguru import logger
from propan.brokers.rabbit import RabbitQueue
from app.entities.address import CreateAddress
from app.entities.cart import (
    CartBase,
    CartUser,
    CartShipping,
    CartPayment,
    CreateCheckoutResponse,
    CreateCreditCardPaymentMethod,
    CreateCreditCardTokenPaymentMethod,
    CreatePixPaymentMethod,
    generate_empty_cart,
    generate_new_cart,
    validate_cache_cart,
)
from app.entities.coupon import CouponResponse
from app.entities.product import ProductCart
from app.entities.user import UserDBGet, UserData
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod


class UserAddressNotFoundError(Exception):
    """User address not found."""


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
        cache.set(str(cart.uuid), cart.model_dump_json())
    return cart


async def add_product_to_cart(
    cart_uuid: str | None,
    product: ProductCart,
    bootstrap: Command,
) -> CartBase:
    """Must add product to new cart and return cart."""
    cache = bootstrap.cache
    product_db = await bootstrap.uow.get_product_by_id(product.product_id)
    logger.info(f'product_db: {product_db}')
    cart = None
    if cart_uuid:
        cart = cache.get(cart_uuid)
    if None or not cart:
        cart = generate_new_cart(
            product=_product_db,
            price=product_db.price,
            quantity=product.quantity,
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
        )
    cache.set(str(cart.uuid), cart.model_dump_json())
    return cart


async def calculate_cart(
    uuid: str,
    cart: CartBase,
    bootstrap: Command,
) -> CartBase:
    """Must calculate cart and return cart."""
    cache = bootstrap.cache
    cache_cart = cache.get(uuid)
    cache_cart = CartBase.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise HTTPException(
            status_code=400,
            detail='Cart uuid is not the same as the cache uuid',
        )
    products_db = await bootstrap.uow.get_products(cart.cart_items)
    cart.get_products_price_and_discounts(products_db)
    if cart.coupon and not (
        coupon := await bootstrap.uow.get_coupon_by_code(cart.coupon)
    ):
        raise HTTPException(
            status_code=400,
            detail='Coupon not found',
        )
    if cart.zipcode:
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
    if cart.cart_items:
        cart.calculate_subtotal(
            discount=coupon.coupon_fee if cart.coupon else 0,
        )
    cache.set(str(cart.uuid), cart.model_dump_json())
    return cart


async def add_user_to_cart(
    uuid: str,
    cart: CartBase,
    token: str,
    bootstrap: Command,
) -> CartUser:
    """Must validate token user if is valid add user id in cart."""
    user = bootstrap.user.get_current_user(token)
    customer_stripe_uuid = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=PaymentGatewayAvailable.STRIPE.name,
        bootstrap=bootstrap,
    )
    customer_mercadopago_uuid = await bootstrap.cart_uow.get_customer(
        user.user_id,
        payment_gateway=PaymentGatewayAvailable.MERCADOPAGO.name,
        bootstrap=bootstrap,
    )
    if not customer_stripe_uuid or not customer_mercadopago_uuid:
        await bootstrap.message.broker.publish(
            {'user_id': user.user_id, 'user_email': user.email},
            queue=RabbitQueue('create_customer'),
        )
    user_data = UserData.model_validate(user)
    cart_user = CartUser(**cart.model_dump(), user_data=user_data)
    cache = bootstrap.cache
    cache.get(uuid)
    cache.set(str(cart.uuid), cart_user.model_dump_json())
    return cart_user


async def add_address_to_cart(
    uuid: str,
    cart: CartUser,
    address: CreateAddress,
    token: str,
    bootstrap: Command,
) -> CartShipping:
    """Must add addresss information to shipping and payment."""
    user = bootstrap.user.get_current_user(token)
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
    bootstrap.cache.set(str(cart.uuid), cart.model_dump_json())
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
    user = bootstrap.user.get_current_user(token)
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
        payment_gateway = 'mercadopago_gateway'
        _payment = getattr(bootstrap.payment, payment_gateway).create_pix(
            amount=int(cache_cart.subtotal),
            customer_id=customer,
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
            customer_id=customer,
            pix_qr_code=qr_code,
            pix_qr_code_base4=qr_code_base64,
            pix_payment_id=payment_id,
        )
        bootstrap.cache.set(str(cart.uuid), cart.model_dump_json())
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
        customer_uuid=customer,
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
        customer_id=customer,
        installments=installments,
    )
    bootstrap.cache.set(str(cart.uuid), cart.model_dump_json())
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
    user = bootstrap.user.get_current_user(token)
    cart = bootstrap.cache.get(uuid)
    cache_cart = CartPayment.model_validate_json(cart)
    if cache_cart.gateway_provider == PaymentGatewayAvailable.STRIPE.name:
        payment_intent = bootstrap.payment.create_payment_intent(
            amount=cache_cart.subtotal,
            currency='brl',
            customer_id=user.customer_id,
            payment_method=cache_cart.payment_method_id,
            installments=cache_cart.installments,
        )
        cache_cart.payment_intent = payment_intent['id']
    bootstrap.cache.set(str(cache_cart.uuid), cache_cart.model_dump_json())
    return cache_cart


async def checkout(
    uuid: str,
    cart: CartPayment,
    token: str,
    bootstrap: Command,
) -> CreateCheckoutResponse:
    """Process payment to specific cart."""
    _ = cart
    user = bootstrap.user.get_current_user(token)
    cache_cart = bootstrap.cache.get(uuid)
    validate_cache_cart(cache_cart)
    cache_cart = CartPayment.model_validate_json(cache_cart)

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
    checkout_task = await bootstrap.message.broker.publish(
        {
            'cart_uuid': uuid,
            'payment_gateway': cache_cart.gateway_provider,
            'payment_method': cache_cart.payment_method,
            'user': user,
        },
        queue=RabbitQueue('checkout'),
        callback=True,
    )
    return CreateCheckoutResponse(
        message=str(checkout_task),
        status='processing',
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
