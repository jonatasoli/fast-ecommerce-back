from sqlalchemy.orm import Session
from fastapi import Header, APIRouter, Depends
from domains import domain_order
from schemas.order_schema import OrderSchema, OrderFullResponse
from endpoints.deps import get_db

order = APIRouter()

@order.get('/order/{id}', status_code=200)
async def get_order(
        *,
        db: Session = Depends(get_db),
        id):
    try:
        return domain_order.get_order(db, id)
    except Exception as e:
        raise e

@order.get('/order/user/{id}', status_code=200)
async def get_order_users_id(
        *,
        db: Session = Depends(get_db),
        id):
    try:
        return domain_order.get_order_users(db, id)
    except Exception as e:
        raise e

@order.put('/order/{id}', status_code= 200)
async def put_order(
        *,
        db: Session = Depends(get_db),
        value: OrderFullResponse,
        id):
    try:
        return domain_order.put_order(db, value, id)
    except Exception as e:
        raise e

@order.post('/order/create_order', status_code= 200)
async def create_order(
                *,
                db: Session = Depends(get_db),
                order_data: OrderSchema
                ):
    return domain_order.create_order(db=db, order_data=order_data)

