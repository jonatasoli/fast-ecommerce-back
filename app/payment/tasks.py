from typing import Any

from fastapi import Depends
from loguru import logger
from sqlalchemy.orm import sessionmaker
from app.entities.cart import CartPayment
from app.entities.payment import PaymentDBUpdate
from app.infra.bootstrap.task_bootstrap import Command, bootstrap
from app.infra.custom_decorators import database_uow
from app.infra.worker import task_message_bus

async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()

async def create_pending_payment(
    order_id: int,
    cart: CartPayment,
    user_id: int,
    bootstrap=bootstrap(),
) -> int:
    """Create a new payment."""
    async with bootstrap.db as session:
        payment = await bootstrap.payment_repository.get_payment_by_order_id(
            order_id
        )
        if not payment:
            payment = await bootstrap.payment_repository.create_payment(
                order_id=order_id,
                cart=cart,
                user_id=user_id,
            )
    return payment.id


async def update_payment(
    payment_id: int,
    payment_status: str,
    bootstrap=bootstrap(),
):
    """Update payment status."""
    async with bootstrap.db as session:
        payment = await bootstrap.payment_repository.update_payment(
            payment_id=payment_id,
            payment=PaymentDBUpdate(status=payment_status),
        )



@task_message_bus.event('create_customer')
@database_uow()
async def create_customer(
    user_id: int,
    bootstrap: Any = Depends(get_bootstrap),
    ) -> None:
    """Create a customer in stripe."""
    user = await bootstrap.user_repository.get_user_by_id(user_id)
    customer = bootstrap.payment.create_customer(email=user.email)
    user.customer_id = customer['id']
    await bootstrap.user_repository.update_user(user_id, user)
    logger.info( f'Customer {user.customer_id} created with success')
