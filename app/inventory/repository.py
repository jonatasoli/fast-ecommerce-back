from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import SessionTransaction
from app.infra.constants import InventoryOperation
from app.infra.models import order


async def increase_inventory(
    product_id: int,
    *,
    quantity: int,
    transaction: SessionTransaction,
) -> order.Inventory:
    """Increase inventory."""
    inventory = order.Inventory(
        product_id=product_id,
        quantity=quantity,
        operation=InventoryOperation.INCREASE,
    )
    transaction.session.add(inventory)
    return inventory

async def total_inventory(
    product_id: int,
    *,
    transaction: SessionTransaction,
        ) -> int:
    """Get total inventory by product_id."""
    products_query = select(func.sum(order.Inventory.quantity)).where(order.Inventory.product_id == product_id)
    products = await transaction.session.execute(products_query)
    total = products.fetchone()
    return total[0]

async def decrease_inventory(
    product_id: int,
    *,
    quantity: int,
    order_id: int,
    transaction: SessionTransaction,
) -> order.Inventory:
    """Decrease product in stock."""
    inventory = order.Inventory(
        product_id=product_id,
        quantity=-quantity,
        operation=InventoryOperation.DECREASE.value,
        order_id=order_id,
        created_at=datetime.now()
    )
    transaction.session.add(inventory)
    await transaction.session.flush()
    return inventory
