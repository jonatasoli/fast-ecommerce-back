from decimal import Decimal
from typing import Any

from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import Command
from app.infra.models import order
from app.order.entities import OrderDBUpdate


async def create_order(
    cart: CartPayment,
    affiliate: str | None,
    discount: Decimal,
    user: Any,
    bootstrap: Command,
) -> int:
    """Create a new order."""
    return await bootstrap.order_uow.uow_create_order(
        cart,
        affiliate=affiliate,
        discount=discount,
        user=user,
        bootstrap=bootstrap,
    )


async def update_order(
    order_update: OrderDBUpdate, bootstrap: Command,
) -> order.Order:
    return await bootstrap.order_uow.uow_update_paid_order(
        order_update,
        bootstrap=bootstrap,
    )


async def create_order_status_step(
    order_id: int,
    status: str,
    bootstrap: Command,
    send_mail: bool = False,
) -> int:
    return await bootstrap.order_uow.uow_create_order_status_step(
        order_id,
        status=status,
        send_mail=send_mail,
        bootstrap=bootstrap,
    )
