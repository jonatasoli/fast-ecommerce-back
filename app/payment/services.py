from app.entities.payment import PaymentNotification, PaymentStatusResponse

from propan.brokers.rabbit import RabbitQueue
from typing import Any


async def update_payment(
    payment_data: PaymentNotification,
    bootstrap: Any,
) -> None:
    """Update payment."""
    payment = bootstrap.payment.get_payment_status(
        payment_id=payment_data.data.id,
        payment_gateway='MERCADOPAGO',
    )
    async with bootstrap.db().begin() as session:
        await bootstrap.payment_repository.update_payment_status(
            payment_data.data.id,
            payment_status=payment['status'],
            transaction=session,
        )
    order_id = ''
    user = None
    if payment['status'] == 'paid':
        await bootstrap.message.broker.publish(
            {
                'mail_to': 'contact@jonatasoliveira.dev',
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification-order-paid'),
        )
    if payment['status'] == 'cancelled':
        await bootstrap.message.broker.publish(
            {
                'mail_to': 'contact@jonatasoliveira.dev',
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification-order-paid'),
        )


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
