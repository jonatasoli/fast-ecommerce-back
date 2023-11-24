from loguru import logger
from app.entities.payment import PaymentNotification, PaymentStatusResponse
from payment.schema import ConfigCreditCardResponse
from fastapi import APIRouter, Depends, status
from app.payment import repository
from app.payment import services
from payment.schema import (
    ConfigCreditCardInDB,
)
from app.infra.bootstrap.payment_bootstrap import Command, bootstrap

payment = APIRouter(
    prefix='/payment',
    tags=['payment'],
)


async def get_bootstrap() -> Command:
    """Get bootstrap."""
    return await bootstrap()


@payment.post(
    '/create-config',
    status_code=status.HTTP_201_CREATED,
    response_model=ConfigCreditCardResponse,
)
def create_config(
    *,
    config_data: ConfigCreditCardInDB,
) -> ConfigCreditCardResponse:
    """Create config."""
    return repository.CreditCardConfig(
        config_data=config_data,
    ).create_installment_config()


@payment.post(
    '/callback',
    status_code=status.HTTP_201_CREATED,
)
async def payment_callback(
    payment_data: PaymentNotification,
    bootstrap: Command = Depends(get_bootstrap),
) -> None:
    """Payment notifications callback."""
    logger.info(payment_data)
    return await services.update_payment(payment_data, bootstrap=bootstrap)


@payment.post(
    '/payment_status',
    status_code=status.HTTP_200_OK,
    response_model=PaymentStatusResponse,
)
async def payment_status(
    gateway_payment_id: int,
    bootstrap: Command = Depends(get_bootstrap),
) -> PaymentStatusResponse:
    """Payment status."""
    return await services.get_payment_status(
        gateway_payment_id,
        bootstrap=bootstrap,
    )
