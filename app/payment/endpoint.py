from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session
from .service import CreditCardConfig, Checkout
from payment.gateway import CreditCardGateway, SlipPaymentGateway
from .schema import CreditCardPayment, SlipPayment, CheckoutReceive, ConfigCreditCard\
, ConfigCreditCardResponse
from endpoints import deps

payment = APIRouter()

@payment.post('/gateway-payment-credit-card', status_code=201)
async def payment_credit_card(
        *,
        db: Session = Depends(deps.get_db),
        payment_data: CreditCardPayment
        ):
    payment = CreditCardGateway(db=db, payment=payment_data).credit_card()
    return payment



@payment.post('/gateway-payment-bank-slip', status_code=201)
def payment_bank_slip(
        *,
        db: Session = Depends(deps.get_db),
        payment_data: SlipPayment
        ):
    payment = SlipPaymentGateway(db, payment=payment_data).slip_payment()
    return payment


@payment.post('/create-config', status_code=201)
def create_config(
        *,
        db: Session = Depends(deps.get_db),
        config_data: ConfigCreditCard
        ):
    _config = CreditCardConfig(db=db, config_data=config_data).create_installment_config()
    return ConfigCreditCardResponse.from_orm(_config)


@payment.post('/checkout', status_code=201)
def checkout(
                *,
                db: Session = Depends(deps.get_db),
                data: CheckoutReceive
        ):
    try:
        checkout_data = data.dict().get('transaction')
        affiliate = data.dict().get('affiliate')
        cupom = data.dict().get('cupom')
        from loguru import logger
        logger.info(checkout_data)
        checkout = Checkout.process_checkout(
                db=db,
                checkout_data=checkout_data,
                affiliate=affiliate
                )
        # import ipdb; ipdb.set_trace()
        return checkout
    except Exception as e:
        raise e