from app.entities.cart import CartBase, generate_new_cart
from app.entities.product import ProductCart
from app.infra.bootstrap import Command


async def add_product_to_cart(
    cart_uuid: str | None,
    product: ProductCart,
    bootstrap: Command,
) -> CartBase:
    """Must add product to new cart and return cart."""
    cache = bootstrap.cache.client()
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
