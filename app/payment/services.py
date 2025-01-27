# ruff: noqa: ANN401
from app.entities.payment import (
    PaymentInDB,
    PaymentNotFoundError,
    PaymentNotification,
    PaymentStatusResponse,
)

from faststream.rabbit import RabbitQueue
from typing import Any
from loguru import logger
from app.payment import repository
from app.report import repository as report_repository

async def update_payment(
    payment_data: PaymentNotification,
    bootstrap: Any,
) -> None:
    """Update payment."""
    order_id, user = None, None
    logger.debug(f'Data Payment {payment_data}')
    logger.debug(f'Data Payment ID {payment_data.data.id}')
    try:
        payment = bootstrap.payment.get_payment_status(
            payment_id=payment_data.data.id,
            payment_gateway='MERCADOPAGO',
        )
    except Exception as err:
        raise PaymentNotFoundError from err
    logger.info(f'Gateway {payment}')
    logger.info(f'Status {payment["status"]}')
    payment_db = None
    async with bootstrap.db().begin() as session:
        payment_db = await bootstrap.payment_repository.update_payment_status(
            payment_data.data.id,
            payment_status=payment['status'],
            transaction=session,
        )
        logger.info(f'Pagamento {payment_db}')
        logger.info(f'Pagamento {payment_db[0].order_id}')
        logger.info(f'Pagamento {payment_db[0].status}')
        user = await bootstrap.user_repository.get_user_by_id(
            payment_db[0].user_id,
            transaction=session,
        )
        order_id = payment_db[0].order_id
    if payment['status'] == 'approved' or payment['status'] == 'authorized':
        logger.debug(f'PAyment DB {payment_db}')
        await report_repository.update_payment_commissions(
            paid_status=True,
            payment_id=payment_db[0].payment_id,
            db=session,
            cancelled_status=False,
        )
        await bootstrap.message.broker.publish(
            {
                'mail_to': user.email,
                'order_id': order_id if order_id else '',
            },
            queue=RabbitQueue('notification_order_paid'),
        )
    if payment['status'] == 'cancelled':
        await report_repository.update_payment_commissions(
            paid_status=False,
            payment_id=payment_db[0].payment_id,
            db=session,
            cancelled_status=True,
        )
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
    if not payment:
        raise PaymentNotFoundError
    return PaymentStatusResponse.model_validate(payment)


async def get_payment(
    gateway_payment_id: int,
    db,
) -> PaymentInDB:
    """Get payment status."""
    async with db().begin() as session:
        payment = await repository.get_payment(
            gateway_payment_id,
            transaction=session,
        )
    return PaymentInDB.model_validate(payment)
