from decimal import Decimal
from typing import Any

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import SessionTransaction
from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import Command, bootstrap
from app.infra.custom_decorators import database_uow
from app.infra.models import order
from app.order.entities import OrderDBUpdate


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()

@database_uow()
async def create_order(
    cart: CartPayment,
    affiliate: str | None,
    discount: Decimal,
    user: Any,
    bootstrap: Command,
    transaction: SessionTransaction,
) -> int:
    """Create a new order."""
    order = await bootstrap.order_repository.get_order_by_cart_uuid(cart.uuid, transaction=transaction)
    affiliate_id = None
    affiliate = await bootstrap.user_repository.get_user_by_username(affiliate, transaction=transaction)
    if affiliate:
        affiliate_id = affiliate.user_id
    if not order:
        order = await bootstrap.order_repository.create_order(
            cart,
            affiliate_id=affiliate_id,
            discount=discount,
            user_id=user['user_id'],
            transaction=transaction,
        )
    for item in cart.cart_items:
        await bootstrap.order_repository.create_order_item(
            discount_price=item.discount_price,
            order_id=order.order_id,
            price=item.price,
            product_id=item.product_id,
            quantity=item.quantity,
            transaction=transaction,
        )

    return order.order_id


@database_uow()
async def update_order(order_update: OrderDBUpdate, transaction: SessionTransaction, bootstrap=bootstrap()) -> order.Order:
    order = await bootstrap.order_repository.update_order(
        order_update,
        transaction=transaction,
    )
    return order


async def create_order_status_step(
    order_id: int,
    status: str,
    transaction: SessionTransaction,
    send_mail: bool = False,
    bootstrap=bootstrap(),
) -> int:
    async with bootstrap.db() as session:
        order_status_step = await bootstrap.order_repository.create_order_status_step(
            order_id=order_id,
            status=status,
            sending=send_mail,
            transaction=transaction,
        )
    return order_status_step.id
