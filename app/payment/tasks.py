from typing import Any
from app.infra.bootstrap.task_bootstrap import bootstrap
from app.infra.worker import task_payment_router


async def create_pending_payment(
    order_id: int,
    payment_intent: Any,
    bootstrap=bootstrap(),
) -> int:
    async with bootstrap.db as session:
        payment = await bootstrap.payment.create_payment(
            order_id=order_id,
            payment_intent=payment_intent,
        )
    return payment.id


def update_payment_status(
    payment_id: int,
    payment_status: str,
    bootstrap=bootstrap(),
):
    return 1


@task_payment_router.event('create_customer')
async def create_customer(user_id: int, bootstrap=bootstrap()) -> None:
    """Create a customer in stripe."""
    async with bootstrap.db as session:
        user = await bootstrap.user.get_user_by_id(session, user_id)
        customer = bootstrap.payment.create_customer(email=user.email)
        user.customer_id = customer['id']
        session.add(user)
        await session.commit()
