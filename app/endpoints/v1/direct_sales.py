from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.payment_schema import CreditCardPayment, SlipPayment
from schemas.order_schema import ProductSchema
from domains import domain_payment 
from domains import domain_order
from endpoints import deps

direct_sales = APIRouter()

@direct_sales.get('/product/{uri}', status_code=200)
async def get_product(uri):
    try:
        return domain_order.get_product(uri)
    except Exception as e:
        raise e


@direct_sales.get('/upsell/{id}', status_code=200)
async def get_upsell_products(id):
    try:
        return True
    except Exception as e:
        raise e


@direct_sales.post('/checkout', status_code=201)
async def checkout():
    try:
        return True
    except Exception as e:
        raise e


@direct_sales.post('/create-product', status_code=201)
async def create_product(
                *,
                db: Session = Depends(deps.get_db),
                product_data: ProductSchema
                ):
    return domain_order.create_product(db=db, product_data=product_data)
