from typing import Any
from app.entities.cart import CartPayment
from app.entities.payment import PaymentDBUpdate
from app.infra.bootstrap.task_bootstrap import bootstrap
from app.infra.worker import task_payment_router


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



@task_payment_router.event('create_customer')
async def create_customer(user_id: int, bootstrap=bootstrap()) -> None:
    """Create a customer in stripe."""
    async with bootstrap.db as session:
        user = await bootstrap.user.get_user_by_id(session, user_id)
        customer = bootstrap.payment.create_customer(email=user.email)
        user.customer_id = customer['id']
        session.add(user)
        await session.commit()
