from fastapi import Header, APIRouter, Depends
from starlette.requests import Request
from sqlalchemy.orm import Session
from loguru import logger

from payment.schema import (
    CreditCardPayment,
    SlipPayment,
    ConfigCreditCardInDB,
    ConfigCreditCardResponse,
)
from schemas.order_schema import ProductSchema, CheckoutReceive, CheckoutSchema
from payment import service
from payment import gateway
from payment import repositories
from payment.service import Checkout
from domains import domain_order
from endpoints import deps

from loguru import logger

payment = APIRouter()


@payment.get("/product/category/{uri}", status_code=200)
async def get_product(*, db: Session = Depends(deps.get_db), uri):
    try:
        return domain_order.get_product(db, uri)
    except Exception as e:
        logger.erro("Erro ao retornar produto {e}")
        raise e


@payment.get("/upsell/{id}", status_code=200)
async def get_upsell_products(id):
    try:
        return True
    except Exception as e:
        logger.error("Erro ao retornar upsell {e}")
        raise e


@payment.post("/checkout", status_code=201)
def checkout(*, db: Session = Depends(deps.get_db), data: CheckoutReceive):
    checkout_data = data.dict().get("transaction")
    affiliate = data.dict().get("affiliate")
    cupom = data.dict().get("cupom")
    logger.info(checkout_data)
    checkout = Checkout(
        db=db, checkout_data=checkout_data, affiliate=affiliate, cupom=cupom
    ).process_checkout()
    return checkout


@payment.post("/create-product", status_code=201)
async def create_product(
    *, db: Session = Depends(deps.get_db), product_data: ProductSchema
):
    product = domain_order.create_product(db=db, product_data=product_data)
    return ProductSchema.from_orm(product)


@payment.post("/create-config", status_code=201)
def create_config(*, config_data: ConfigCreditCardInDB):
    _config = repositories.CreditCardConfig(
        config_data=config_data
    ).create_installment_config()
    return ConfigCreditCardResponse.from_orm(_config)


@payment.post("/gateway-payment-credit-card", status_code=201)
async def payment_credit_card(*, payment_data: CreditCardPayment):
    payment = gateway.credit_card_payment(payment=payment_data)
    return payment


@payment.post("/gateway-payment-bank-slip", status_code=201)
def payment_bank_slip(*, payment_data: SlipPayment):
    payment = gateway.slip_payment(payment=payment_data)
    return payment
