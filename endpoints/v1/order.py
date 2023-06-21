from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header
from loguru import logger
from sqlalchemy.orm import Session

from constants import OrderStatus
from domains import domain_order
from endpoints.deps import get_db
from gateway.payment_gateway import return_transaction
from job_service.service import get_session
from models.order import Order
from models.transaction import Payment
from schemas.order_schema import (
    OrderFullResponse,
    OrderSchema,
    TrackingFullResponse,
)

order = APIRouter(
    prefix="/order",
    tags=["order"],
)


@order.get('/{id}', status_code=200)
async def get_order(*, db: Session = Depends(get_db), id):
    try:
        return domain_order.get_order(db, id)
    except Exception as e:
        raise e


@order.get('/user/{id}', status_code=200)
async def get_order_users_id(*, db: Session = Depends(get_db), id):
    try:
        return domain_order.get_order_users(db, id)
    except Exception as e:
        raise e


@order.get('/orders', status_code=200)
async def get_orders_paid(
    dates: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    try:
        return domain_order.get_orders_paid(db, dates, status, user_id)
    except Exception as e:
        raise e


@order.put('/{id}', status_code=200)
async def put_order(
    *, db: Session = Depends(get_db), value: OrderFullResponse, id
):
    try:
        return domain_order.put_order(db, value, id)
    except Exception as e:
        raise e


@order.put('/tracking_number/{id}', status_code=200)
async def put_trancking_number(
    id: int,
    value: TrackingFullResponse,
    db: Session = Depends(get_db),
):
    try:
        return domain_order.put_trancking_number(db, value, id)
    except Exception as e:
        raise e


@order.post('/check_order/{id}', status_code=200)
async def put_trancking_number(
    id: int, check: bool, db: Session = Depends(get_db)
):
    try:
        return domain_order.checked_order(db, id, check)
    except Exception as e:
        raise e


@order.post('/create_order', status_code=200)
async def create_order(
    *, db: Session = Depends(get_db), order_data: OrderSchema
):
    return domain_order.create_order(db=db, order_data=order_data)


@order.post('/update-payment-and-order-status', status_code=200)
def order_status():
    db = get_session()
    orders = db.query(Order).filter(Order.id.isnot(None))
    for order in orders:
        return {
            'order_id': order.id,
            'payment_id': order.payment_id,
            'order_status': order.order_status,
        }


def check_status_pedding():
    data = order_status()
    logger.debug(data)
    if data.get('order_status') == 'pending':
        return 'pending'


def status_pending():
    data = order_status()
    logger.debug(data)
    db = get_session()
    payment = db.query(Payment).filter_by(id=data.get('payment_id')).first()
    return return_transaction(payment.gateway_id)


def status_paid():
    gateway = status_pending()
    data = order_status()
    logger.debug(gateway.get('status'))
    if (
        gateway.get('status') == 'paid'
        and data.get('order_status') == 'pending'
    ):
        logger.debug(data)
        data['order_status'] = OrderStatus.PAYMENT_PAID.value
        logger.debug(data)
        return data


def alternate_status(status):
    order_status = {'pending': status_pending, 'paid': status_paid}
    return order_status[status]
