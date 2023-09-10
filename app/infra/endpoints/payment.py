from app.infra.deps import get_db
from payment.schema import InstallmentSchema, ResponseGateway
from payment.schema import ConfigCreditCardResponse, InstallmentSchema
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from domains import domain_order
from app.infra import deps
from payment import gateway, repositories
from payment.schema import (
    ConfigCreditCardInDB,
    CreditCardPayment,
    SlipPayment,
)
from payment.service import Checkout
from schemas.order_schema import CheckoutReceive

payment = APIRouter(
    prefix='/payment',
    tags=['payment'],
)
cart = APIRouter(
    prefix='/cart',
    tags=['cart'],
)


@cart.get('/upsell/{id}', status_code=200)
async def get_upsell_products() -> None:
    """Get upsell products."""
    try:
        return True
    except Exception:
        logger.error('Erro ao retornar upsell {e}')
        raise


@cart.post('/checkout', status_code=201, response_model=CheckoutReceive)
def checkout(
    *,
    db: Session = Depends(deps.get_db),
    data: CheckoutReceive,
) -> CheckoutReceive:
    """Checkout."""
    checkout_data = data.dict().get('transaction')
    affiliate = data.dict().get('affiliate')
    cupom = data.dict().get('cupom')
    logger.info(checkout_data)
    logger.info(affiliate)
    return Checkout(
        db=db,
        checkout_data=checkout_data,
        affiliate=affiliate,
        cupom=cupom,
    ).process_checkout()


@payment.post(
    '/create-config', status_code=201, response_model=ConfigCreditCardResponse,
)
def create_config(
    *, config_data: ConfigCreditCardInDB,
) -> ConfigCreditCardResponse:
    """Create config."""
    return repositories.CreditCardConfig(
        config_data=config_data,
    ).create_installment_config()


@payment.post(
    '/gateway-payment-credit-card',
    status_code=201,
    response_model=ResponseGateway,
)
async def payment_credit_card(
    *, payment_data: CreditCardPayment,
) -> ResponseGateway:
    """Payment credit card."""
    return gateway.credit_card_payment(payment=payment_data)


@payment.post('/gateway-payment-bank-slip', status_code=201)
def payment_bank_slip(*, payment_data: SlipPayment) -> None:
    """Payment bank slip."""
    return gateway.slip_payment(payment=payment_data)


@cart.post('/cart/installments', status_code=200)
async def get_installments(
    *,
    db: Session = Depends(get_db),
    cart: InstallmentSchema,
) -> None:
    """Get installments."""
    try:
        return domain_order.get_installments(db, cart=cart)
    except Exception as e:
        logger.error(f'Erro ao coletar o parcelamento - {e}')
        raise
