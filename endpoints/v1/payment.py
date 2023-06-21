from endpoints.deps import get_db
from payment.schema import InstallmentSchema
from fastapi import APIRouter, Depends, Header
from loguru import logger
from sqlalchemy.orm import Session

from domains import domain_order
from endpoints import deps
from payment import gateway, repositories, service
from payment.schema import (
    ConfigCreditCardInDB,
    ConfigCreditCardResponse,
    CreditCardPayment,
    SlipPayment,
)
from payment.service import Checkout
from schemas.order_schema import CheckoutReceive, CheckoutSchema, ProductSchema

payment = APIRouter(
    prefix='/payment',
    tags=['payment'],
)
cart= APIRouter(
    prefix='/cart',
    tags=['cart'],
)


@cart.get('/upsell/{id}', status_code=200)
async def get_upsell_products(id):
    try:
        return True
    except Exception as e:
        logger.error('Erro ao retornar upsell {e}')
        raise e


@cart.post('/checkout', status_code=201)
def checkout(*, db: Session = Depends(deps.get_db), data: CheckoutReceive):
    checkout_data = data.dict().get('transaction')
    affiliate = data.dict().get('affiliate')
    cupom = data.dict().get('cupom')
    logger.info(checkout_data)
    logger.info(affiliate)
    checkout = Checkout(
        db=db, checkout_data=checkout_data, affiliate=affiliate, cupom=cupom
    ).process_checkout()
    return checkout


@payment.post('/create-product', status_code=201)
async def create_product(
    *, db: Session = Depends(deps.get_db), product_data: ProductSchema
):
    product = domain_order.create_product(db=db, product_data=product_data)
    return ProductSchema.from_orm(product)


@payment.post('/create-config', status_code=201)
def create_config(*, config_data: ConfigCreditCardInDB):
    _config = repositories.CreditCardConfig(
        config_data=config_data
    ).create_installment_config()
    return ConfigCreditCardResponse.from_orm(_config)


@payment.post('/gateway-payment-credit-card', status_code=201)
async def payment_credit_card(*, payment_data: CreditCardPayment):
    payment = gateway.credit_card_payment(payment=payment_data)
    return payment


@payment.post('/gateway-payment-bank-slip', status_code=201)
def payment_bank_slip(*, payment_data: SlipPayment):
    payment = gateway.slip_payment(payment=payment_data)
    return payment

@cart.post('/cart/installments', status_code=200)
async def get_installments(
    *, db: Session = Depends(get_db), cart: InstallmentSchema
):
    try:
        return domain_order.get_installments(db, cart=cart)
    except Exception as e:
        logger.error(f'Erro ao coletar o parcelamento - {e}')
        raise e
