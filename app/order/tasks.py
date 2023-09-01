from decimal import Decimal
from app.entities.cart import CartPayment
from app.infra.bootstrap.task_bootstrap import bootstrap


async def create_order(
    cart: CartPayment,
    affiliate: str | None,
    discount: Decimal,
    boostrap=bootstrap(),
) -> int:
    async with boostrap.db() as session:
        order = await bootstrap.order_repository.create_order(
            session,
            cart,
            affiliate,
            discount,
        )

    return order.id


def update_order(order_id: int, order_status: str, bootstrap=bootstrap()):
    return 1


def create_order_status_step(
    order_id: int,
    status: str,
    send_mail: bool = False,
    bootstrap=bootstrap(),
) -> int:
    return 1
