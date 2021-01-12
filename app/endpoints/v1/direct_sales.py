from fastapi import Header, APIRouter, Depends
from starlette.requests import Request
from sqlalchemy.orm import Session
from loguru import logger

from schemas.payment_schema import CreditCardPayment, SlipPayment
from schemas.order_schema import ProductSchema, CheckoutReceive, CheckoutSchema
from domains import domain_payment 
from domains import domain_order
from endpoints import deps

direct_sales = APIRouter()

@direct_sales.get('/product/{uri}', status_code=200)
async def get_product(
        *,
        db: Session = Depends(deps.get_db),
        uri):
    try:
        return domain_order.get_product(db, uri)
    except Exception as e:
        raise e


@direct_sales.get('/upsell/{id}', status_code=200)
async def get_upsell_products(id):
    try:
        return True
    except Exception as e:
        raise e


# @direct_sales.post('/checkout', status_code=201)
# def checkout(
#                 *,
#                 db: Session = Depends(deps.get_db),
#                 data: CheckoutReceive
#         ):
#     try:
#         checkout_data = data.dict().get('transaction')
#         affiliate = data.dict().get('affiliate')
#         cupom = data.dict().get('cupom')
#         from loguru import logger
#         logger.info(checkout_data)
#         checkout = domain_payment.process_checkout(
#                 db=db,
#                 checkout_data=checkout_data,
#                 affiliate=affiliate,
#                 cupom=cupom)
#         # import ipdb; ipdb.set_trace()
#         return checkout
#     except Exception as e:
#         raise e


@direct_sales.post('/create-product', status_code=201)
async def create_product(
                *,
                db: Session = Depends(deps.get_db),
                product_data: ProductSchema
                ):
    product = domain_order.create_product(db=db, product_data=product_data)
    return ProductSchema.from_orm(product)
