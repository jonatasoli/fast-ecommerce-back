from typing import Any

from sqlalchemy.orm import SessionTransaction
from app.infra.custom_decorators import database_uow
from app.user import repository as user_repository


@database_uow()
async def uow_create_customer(
    user_id: int,
    *,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> str:
    """Create a new customer."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    user = await user_repository.get_user_by_id(
        user_id, transaction=transaction,
    )
    customer = bootstrap.payment.create_customer(email=user.email)
    user.customer_id = customer['id']
    updated_user = await user_repository.update_user(
        user_id, user=user, transaction=transaction,
    )
    return updated_user.customer_id
