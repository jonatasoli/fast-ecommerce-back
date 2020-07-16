from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.payment_schema import CreditCardPayment, SlipPayment
from domains import domain_payment 
from endpoints import deps

direct_sales = APIRouter()

@direct_sales.get('/product/{uri}')
async def get_product(uri):
    try:
        pass
    except Exception as e:
        raise e


@direct_sales.get('/upsell/{id}')
async def get_upsell_products(id):
    try:
        pass
    except Exception as e:
        raise e


@direct_sales.post('/checkout')
async def checkout():
    try:
        pass
    except Exception as e:
        raise e

