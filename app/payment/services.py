# ruff: noqa: ANN401
from contextlib import suppress
from app.entities.payment import (
    PaymentInDB,
    PaymentNotFoundError,
    PaymentStatusResponse,
)

from faststream.rabbit import RabbitQueue
from typing import Any
from loguru import logger
from app.infra.constants import PaymentGatewayAvailable
from app.infra.database import get_async_session
from app.infra.payment_gateway.mercadopago_gateway import PaymentStatusError
from app.payment import repository
from app.report import repository as report_repository
from app.infra.payment_gateway import payment_gateway

async def update_payment(
    payment_data,
    bootstrap,
) -> None:
    """Update payment."""
    order_id, user = None, None
    logger.debug(f'Data Payment {payment_data}')
    payment_data = await payment_data.json()
    logger.debug(f'Data Payment ID {payment_data.get('data')}')
    logger.debug(f'Data Payment ID {payment_data.get('id')}')
    try:
        payment = bootstrap.payment.get_payment_status(
            payment_id=payment_data.get('id'),
            payment_gateway='MERCADOPAGO',
        )
    except Exception as err:
        raise PaymentNotFoundError from err
    logger.info(f'Gateway {payment}')
    logger.info(f'Status {payment["status"]}')
    payment_db = None
    async with bootstrap.db().begin() as session:
        payment_db = await bootstrap.payment_repository.update_payment_status(
            payment_data.get('id'),
            payment_status=payment['status'],
            authorization_status=payment['authorization_code'],
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


async def update_pending_payments(db=get_async_session):
    """Get all peding payments and update."""
    async with db().begin() as session:
        payments = await repository.get_pending_payments(
            PaymentGatewayAvailable.MERCADOPAGO.value,
            transaction=session,
        )
        for payment in payments.all():
            logger.debug('Payment search start')
            with suppress(PaymentNotFoundError, PaymentStatusError):
                logger.debug(payment.gateway_payment_id)
                payment_in_gateway = await get_payment_gateway_status(
                    gateway_payment_id=payment.gateway_payment_id,
                )
                if status := payment_in_gateway.get('status'):
                    authorization_status = payment_in_gateway.get('authorization_code')
                    message = 'Not computed'
                    if authorization_status:
                        message = authorization_status
                    payment.status = status
                    payment.authorization = message
                    logger.debug('Add Payment with new status')
                    session.add(payment)
                await session.flush()
        logger.debug('commit all transactions')
        await session.commit()


async def get_payment_gateway_status(
    gateway_payment_id: int | str,
):
    """Get payment status."""
    payment = payment_gateway.get_payment_status(
        payment_id=gateway_payment_id,
        payment_gateway=PaymentGatewayAvailable.MERCADOPAGO.value,

    )
    if not payment:
        raise PaymentNotFoundError
    return payment


async def get_payment_status(
    gateway_payment_id: int | str,
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
    gateway_payment_id: int | str,
    db,
) -> PaymentInDB:
    """Get payment status."""
    async with db().begin() as session:
        payment = await repository.get_payment(
            gateway_payment_id,
            transaction=session,
        )
    return PaymentInDB.model_validate(payment)
