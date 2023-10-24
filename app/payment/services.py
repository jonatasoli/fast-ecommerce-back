from app.entities.payment import PaymentStatusResponse
from typing import Any


async def update_payment():
    """Update payment."""
    ...


async def get_payment_status(
    gateway_payment_id: int,
    bootstrap: Any,
) -> PaymentStatusResponse:
    """Get payment status."""
    async with bootstrap.db().begin() as session:
        payment = await bootstrap.payment_repository.get_payment(
            gateway_payment_id,
            transaction=session,
        )
    return PaymentStatusResponse.model_validate(payment)
