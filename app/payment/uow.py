from typing import Any

from sqlalchemy.orm import SessionTransaction
from app.entities.cart import CartPayment
from app.entities.payment import PaymentDBUpdate
from app.infra.custom_decorators import database_uow
from app.payment import repository as payment_repository


@database_uow()
async def uow_create_pending_payment(
    order_id: int,
    *,
    cart: CartPayment,
    user_id: int,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> int:
    """Create a new payment."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    payment = await payment_repository.get_payment_by_order_id(
        order_id,
        transaction=transaction,
    )
    if not payment:
        payment = await payment_repository.create_payment(
            cart,
            order_id=order_id,
            user_id=user_id,
            transaction=transaction,
        )
    return payment.payment_id


@database_uow()
async def uow_update_payment(
    payment_id: int,
    *,
    payment_status: str,
    bootstrap: Any,
    transaction: SessionTransaction | None,
) -> None:
    """Update payment status."""
    if not transaction:
        msg = 'Transaction must be provided'
        raise ValueError(msg)
    await payment_repository.update_payment(
        payment_id,
        payment=PaymentDBUpdate(status=payment_status),
        transaction=transaction,
    )
