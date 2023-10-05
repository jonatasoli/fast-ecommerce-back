from app.infra.deps import get_db
from payment.schema import InstallmentSchema, ResponseGateway
from payment.schema import ConfigCreditCardResponse, InstallmentSchema
from fastapi import APIRouter, Depends
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
