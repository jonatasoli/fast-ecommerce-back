from typing import Any

from sqlalchemy.orm import SessionTransaction
from app.infra.custom_decorators import database_uow
from app.user import repository as user_repository
from app.payment import repository as payment_repository


@database_uow()
async def uow_create_customer(
    user_id: int,
    *,
    payment_gateway: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> str:
    """Create a new customer."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    user = await user_repository.get_user_by_id(
        user_id,
        transaction=transaction,
    )
    customer = bootstrap.payment[payment_gateway].create_customer(email=user.email, payment_gateway=payment_gateway)
    customer_db = await payment_repository.create_customer(
        user_id=user_id,
        customer_uuid=customer['id'],
        payment_gateway=payment_gateway,
        transaction=transaction,

    )
    return customer_db.customer_id
