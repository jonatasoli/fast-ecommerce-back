from typing import Any

from loguru import logger
from app.entities.cart import CartPayment
from app.entities.payment import PaymentDBUpdate
from app.infra.bootstrap.task_bootstrap import Command, bootstrap
from app.infra.worker import task_message_bus


async def create_pending_payment(
    order_id: int,
    *,
    cart: CartPayment,
    user_id: int,
    bootstrap: Any,
) -> int:
    """Create a new payment."""
    payment_id = await bootstrap.payment_uow.uow_create_pending_payment(
        order_id,
        cart=cart,
        user_id=user_id,
        bootstrap=bootstrap,
    )
    return payment_id


async def update_payment(
    payment_id: int,
    payment_status: str,
    bootstrap:Any,
):
    """Update payment status."""
    await bootstrap.payment_uow.uow_update_payment(
        payment_id,
        payment_status=payment_status,
        bootstrap=bootstrap,
    )


@task_message_bus.event('create_customer')
async def create_customer(
    user_id: int,
    bootstrap: Any,
) -> None:
    """Create a customer in stripe."""
    customer_id = await bootstrap.payment_uow.uow_create_customer(
        user_id,
        bootstrap=bootstrap,
    )
    logger.info(f'Customer {customer_id} from {user_id} created with success')
