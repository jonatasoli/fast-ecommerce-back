from sqlalchemy.orm import Session
from fastapi import Header, APIRouter, Depends
from domains import domain_order
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
