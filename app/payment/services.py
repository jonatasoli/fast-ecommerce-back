from app.entities.payment import PaymentNotification, PaymentStatusResponse

from propan.brokers.rabbit import RabbitQueue
from typing import Any
from loguru import logger


async def update_payment(
    payment_data: PaymentNotification,
    bootstrap: Any,
) -> None:
    """Update payment."""
    order_id, user = None, None
    payment = bootstrap.payment.get_payment_status(
        payment_id=payment_data.data.id,
        payment_gateway='MERCADOPAGO',
    )
    async with bootstrap.db().begin() as session:
        payment_db = await bootstrap.payment_repository.update_payment_status(
            payment_data.data.id,
            payment_status=payment['status'],
            transaction=session,
        )
        logger.info(f'Pagamento {payment_db}')
        user = await bootstrap.user_repository.get_user_by_id(
            payment_db[0].user_id,
            transaction=session,
        )
        order_id = payment_db[0].order_id
    if payment['status'] == 'authorized':
        await bootstrap.message.broker.publish(
            {
                'mail_to': user.email,
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification_order_paid'),
        )
    if payment['status'] == 'cancelled':
        await bootstrap.message.broker.publish(
            {
                'mail_to': user.email,
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification_order_paid'),
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
