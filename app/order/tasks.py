from typing import Any

from fastapi import Depends

from app.entities.cart import CartPayment
from app.entities.coupon import CouponInDB
from app.infra.bootstrap.task_bootstrap import Command
from app.infra.models import OrderDB
from app.entities.order import OrderDBUpdate
from app.infra.worker import task_message_bus
from app.infra.bootstrap.task_bootstrap import bootstrap


async def create_order(
    cart: CartPayment,
    affiliate_id: int | None,
    coupon: CouponInDB | None,
    user: Any,
    bootstrap: Command,
) -> int:
    """Create a new order."""
    return await bootstrap.order_uow.uow_create_order(
        cart,
        affiliate_id=affiliate_id,
        coupon=coupon,
        user=user,
        bootstrap=bootstrap,
    )


async def update_order(
    order_update: OrderDBUpdate,
    bootstrap: Command,
) -> OrderDB:
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


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@task_message_bus.subscriber('cancel_order')
async def cancel_order_task(
    order_id: int,
    bootstrap: Any = Depends(get_bootstrap),
) -> None:
    """Cancel order task."""
