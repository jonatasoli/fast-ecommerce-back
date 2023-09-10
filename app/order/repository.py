import abc
from decimal import Decimal
from typing import Self
from sqlalchemy import update

from sqlalchemy.orm import SessionTransaction, sessionmaker
from datetime import datetime

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.infra.constants import OrderStatus
from app.infra.models.order import Order, OrderItems, OrderStatusSteps
from app.order.entities import OrderDBUpdate


async def create_order(
    cart: CartPayment,
    *,
    discount: Decimal,
    user_id: int,
    transaction: SessionTransaction,
    affiliate_id: int | None,
) -> Order:
    """Create a new order."""
    _order = Order(
        affiliate_id=affiliate_id,
        cart_uuid=str(cart.uuid),
        customer_id=cart.customer_id,
        discount=discount,
        last_updated=datetime.now(),
        order_date=datetime.now(),
        order_status=OrderStatus.PAYMENT_PENDING.value,
        user_id=user_id,
    )
    transaction.session.add(_order)
    await transaction.session.flush()
    return _order


async def get_order_by_id(
    order_id: int, *, transaction: SessionTransaction
) -> Order:
    """Get an order by its id."""
    order_query = select(Order).where(
        Order.order_id == order_id,
    )
    return await transaction.session.scalar(order_query)


async def update_order(
    order: OrderDBUpdate, transaction: SessionTransaction
) -> Order:
    """Update an existing order."""
    update_query = (
        update(Order)
        .where(Order.order_id == order.order_id)
        .values(
            **order.model_dump(
                exclude_unset=True,
                exclude={'order_id'},
            ),
            last_updated=datetime.now(),
        )
        .returning(Order)
    )
    return await transaction.session.execute(update_query)


async def get_order_by_cart_uuid(
    cart_uuid: str,
    *,
    transaction: SessionTransaction,
) -> Order | None:
    """Get an order by its cart uuid."""
    order_query = select(Order).where(Order.cart_uuid == str(cart_uuid))
    order_db = await transaction.session.execute(order_query)
    return order_db.scalar_one_or_none()


async def create_order_status_step(
    order_id: int,
    *,
    status: str,
    transaction: SessionTransaction,
    sending: bool = False,
) -> int:
    """Create a new order status step."""
    order_status_step = OrderStatusSteps(
        order_id=order_id,
        status=status,
        sending=sending,
        active=True,
        last_updated=datetime.now(),
    )
    transaction.session.add(order_status_step)
    await transaction.session.flush()
    return order_status_step.order_status_steps_id


async def create_order_item(
    order_id: int,
    *,
    product_id: int,
    quantity: int,
    price: Decimal,
    discount_price: Decimal,
    transaction: SessionTransaction,
) -> int:
    """Create a new order item."""
    order_item = OrderItems(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        price=price,
        discount_price=discount_price,
    )
    transaction.session.add(order_item)
    transaction.session.flush()
    return order_item.order_items_id
