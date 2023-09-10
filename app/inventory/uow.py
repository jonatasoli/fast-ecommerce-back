from typing import Any
from sqlalchemy.orm import SessionTransaction
from app.entities.cart import CartPayment
from app.infra.custom_decorators import database_uow
from app.inventory import repository as inventory_repository


@database_uow()
async def uow_decrease_inventory(
    cart: CartPayment,
    order_id: int,
    bootstrap: Any,
    transaction: SessionTransaction,
) -> None:
    """Decrease inventory by specific cart."""
    if not transaction:
        raise Exception('Transaction not found')
    for item in cart.cart_items:
        await inventory_repository.decrease_inventory(
            item.product_id,
            quantity=item.quantity,
            order_id=order_id,
            transaction=transaction,
        )
        total = await inventory_repository.total_inventory(
            item.product_id,
            transaction=transaction,
        )
        if total < 0:
            raise Exception('Product not available')
