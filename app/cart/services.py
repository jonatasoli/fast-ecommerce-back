from fastapi import HTTPException
from app.entities.address import CreateAddress
from app.entities.cart import (
    CartBase,
    CartUser,
    CartShipping,
    CartPayment,
    CreatePaymentMethod,
    generate_empty_cart,
    generate_new_cart,
)
from app.entities.product import ProductCart
from app.entities.user import UserData
from app.infra.bootstrap import Command


class UserAddressNotFoundError(Exception):
    """User address not found."""

    ...


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
    cart = None
    if cart_uuid:
        cart = cache.get(cart_uuid)
    if None or not cart:
        cart = generate_new_cart(
            product=product,
            price=product_db.price,
            quantity=product.quantity,
        )
    else:
        cart = cache.get(cart_uuid)
        cart = CartBase.model_validate_json(cart)
        cart.add_product(
            product_id=product.product_id,
            quantity=product.quantity,
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
        freight_cart = await bootstrap.freight.calculate_volume_weight(
            cart.zipcode,
            products=products_db,
        )
        cart.freight_price = await bootstrap.freight.get_freight(
            freight_cart=freight_cart,
            zipcode=cart.zipcode,
        )
    cart.calculate_subtotal(discount=coupon.coupon_fee if cart.coupon else 0)
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
    if not address_id:
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
    cart: CartShipping,
    payment: CreatePaymentMethod,
    token: str,
    bootstrap: Command,
    payment_method: str = 'card',
) -> CartPayment:
    """Must add payment information and create token in payment gateway."""
    _ = token
    cache_cart = bootstrap.cache.get(uuid)
    cache_cart = CartShipping.model_validate_json(cache_cart)
    if cache_cart.uuid != cart.uuid:
        raise HTTPException(
            status_code=400,
            detail='Cart uuid is not the same as the cache uuid',
        )
    payment = bootstrap.payment.create_payment_method(payment)
    cart = CartPayment(
        **cart.model_dump(),
        payment_method=payment_method,
        payment_method_id=payment.id,
    )
    bootstrap.cache.set(str(cart.uuid), cart.model_dump_json())
    await bootstrap.uow.update_payment_method_to_user(cart.user.id, payment.id)
    return cart


async def preview(
    uuid: str,
    token: str,
    bootstrap: Command,
) -> CartPayment:
    """Must get address id and payment token to show in cart."""
    _ = token
    cart = bootstrap.cache.get(uuid)
    return CartPayment.model_validate_json(cart)


async def checkout(
    uuid: str,
    cart: CartPayment,
    token: str,
    bootstrap: Command,
) -> None:
    """Process payment to specific cart."""
    _ = token, cart
    cache_cart = bootstrap.cache.get(uuid)
    if not cart:
        raise HTTPException(
            status_code=400,
            detail='Cart not found',
        )
    bootstrap.publish.checkout.apply_async(args=[cache_cart.uuid])
