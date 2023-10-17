from loguru import logger
from app.entities.payment import PaymentNotification
from app.infra.deps import get_db
from payment.schema import InstallmentSchema, ResponseGateway
from payment.schema import ConfigCreditCardResponse, InstallmentSchema
from fastapi import APIRouter, Depends, status
from payment import repositories
from payment.schema import (
    ConfigCreditCardInDB,
)

payment = APIRouter(
    prefix='/payment',
    tags=['payment'],
)


@payment.post(
    '/create-config',
    status_code=201,
    response_model=ConfigCreditCardResponse,
)
def create_config(
    *,
    config_data: ConfigCreditCardInDB,
) -> ConfigCreditCardResponse:
    """Create config."""
    return repositories.CreditCardConfig(
        config_data=config_data,
    ).create_installment_config()


@payment.post(
    '/callback',
    status_code=status.HTTP_201_CREATED,
)
def payment_callback(payment_data: PaymentNotification):
    """Payment notifications callback."""
    logger.info(payment_data)
    ...
