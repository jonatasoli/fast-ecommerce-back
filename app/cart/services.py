from app.entities.cart import CartBase, generate_new_cart
from app.entities.product import ProductCart
from app.infra.bootstrap import Command


async def add_product_to_cart(
    cart_uuid: str | None,
    product: ProductCart,
    bootstrap: Command,
) -> CartBase:
    """Must add product to new cart and return cart."""
    product_db = await bootstrap.uow.get_product_by_id(product.product_id)
    cart = None
    if cart_uuid:
        cart = bootstrap.cache.get(cart_uuid)

    if None or not cart:
        cart = generate_new_cart(product_db, quantity=product.quantity)
    else:
        cart = bootstrap.cache.get(cart_uuid)
        cart = CartBase.parse_raw(cart)
        cart.add_product(
            product_id=product.product_id,
            quantity=product.quantity,
        )
    bootstrap.cache.set(str(cart.uuid), cart.model_dump_json())
    return cart
