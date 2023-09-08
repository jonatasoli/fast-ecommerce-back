from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import bootstrap


async def decrease_inventory(cart: CartPayment) -> None:
    """Decrease inventory by specific cart."""
    async with bootstrap.db() as session:
        for item in cart.items:
            await bootstrap.inventory_repository.decrease_inventory(
                item.product_id,
                item.quantity,
            )
            product = await bootstrap.inventory_repository.total_inventory(
                item.product_id,
            )
            if product.quantity < 0:
                raise Exception('Product not available')
            await bootstrap.inventory_repository.commit()
