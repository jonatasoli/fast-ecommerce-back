from decimal import Decimal
from typing import Any

from fastapi import Depends
from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import Command, bootstrap
from app.infra.models import order
from app.order.entities import OrderDBUpdate


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


async def create_order(
    cart: CartPayment,
    affiliate: str | None,
    discount: Decimal,
    bootstrap: Command,
) -> int:
    import ipdb; ipdb.set_trace()
    async with bootstrap.db() as session:
        # order_repository = bootstrap.order_repository(session)
        order = await bootstrap.order_repository.get_order_by_cart_uuid(cart.uuid)
        if not order:
            order = await bootstrap.order_repository.create_order(
                session,
                cart,
                affiliate,
                discount,
            )

    return order.id


async def update_order(order_update: OrderDBUpdate, bootstrap=bootstrap()) -> order.Order:
    async with bootstrap.db() as session:
        order = await bootstrap.order_repository.update_order(
            order_update,
        )
    return order


async def create_order_status_step(
    order_id: int,
    status: str,
    send_mail: bool = False,
    bootstrap=bootstrap(),
) -> int:
    async with bootstrap.db() as session:
        order_status_step = await bootstrap.order_repository.create_order_status_step(
            order_id=order_id,
            status=status,
            sending=send_mail,
        )
    return order_status_step.id
