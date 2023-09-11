from typing import Any
from app.entities.cart import CartPayment


async def decrease_inventory(
    cart: CartPayment,
    order_id: int,
    bootstrap: Any,
) -> None:
    """Decrease inventory by specific cart."""
    await bootstrap.inventory_uow.uow_decrease_inventory(
        cart,
        order_id=order_id,
        bootstrap=bootstrap,
    )
