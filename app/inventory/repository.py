from datetime import datetime, UTC
from sqlalchemy import func, select
from sqlalchemy.orm import SessionTransaction
from app.infra.constants import InventoryOperation
from app.infra import models


async def increase_inventory(
    product_id: int,
    *,
    quantity: int,
    transaction: SessionTransaction,
) -> models.InventoryDB:
    """Increase inventory."""
    inventory = models.InventoryDB(
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
    products_query = select(func.sum(models.InventoryDB.quantity)).where(
        models.InventoryDB.product_id == product_id,
    )
    products = await transaction.session.execute(products_query)
    total = products.fetchone()
    return total[0]


async def decrease_inventory(
    product_id: int,
    *,
    quantity: int,
    order_id: int,
    transaction: SessionTransaction,
) -> models.InventoryDB:
    """Decrease product in stock."""
    inventory = models.InventoryDB(
        product_id=product_id,
        quantity=-quantity,
        operation=InventoryOperation.DECREASE.value,
        order_id=order_id,
        created_at=datetime.now(tz=UTC),
    )
    transaction.session.add(inventory)
    await transaction.session.flush()
    return inventory
