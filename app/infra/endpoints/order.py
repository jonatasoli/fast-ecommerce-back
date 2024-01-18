from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.orm import Session

from constants import OrderStatus
from app.order import services
from app.infra.deps import get_db
from gateway.payment_gateway import return_transaction
from job_service.service import get_session
from app.infra.models import PaymentDB, OrderDB
from schemas.order_schema import (
    OrderFullResponse,
    OrderSchema,
    TrackingFullResponse,
    OrderUserListResponse,
)

order = APIRouter(
    prefix='/order',
    tags=['order'],
)


@order.get('/{id}', status_code=200)
async def get_order(
    *,
    db: Session = Depends(get_db),
    id: int,
) -> list[OrderUserListResponse]:
    """Get order."""
    try:
        return services.get_order(db, id)
    except Exception as e:
        logger.error(e)
        raise


@order.get('/user/{id}', status_code=200)
async def get_order_users_id(
    *,
    db: Session = Depends(get_db),
    id: None,
) -> None:
    """Get order users id."""
    try:
        return services.get_order_users(db, id)
    except Exception:
        raise


@order.get('/orders', status_code=200)
async def get_orders_paid(
    dates: str | None = None,
    status: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> None:
    """Get orders paid."""
    try:
        return services.get_orders_paid(db, dates, status, user_id)
    except Exception:
        raise


@order.put('/{id}', status_code=200)
async def put_order(
    *,
    db: Session = Depends(get_db),
    value: OrderFullResponse,
    id: int,
) -> None:
    """Put order."""
    try:
        return services.put_order(db, value, id)
    except Exception:
        raise


@order.put('/tracking_number/{id}', status_code=200)
async def put_trancking_number(
    id: int,
    value: TrackingFullResponse,
    db: Session = Depends(get_db),
) -> None:
    """Put trancking number."""
    try:
        return services.put_trancking_number(db, value, id)
    except Exception:
        raise


@order.post('/check_order/{id}', status_code=200)
async def put_trancking_number(
    id: int,
    check: bool,
    db: Session = Depends(get_db),
) -> int:
    """Put trancking number."""
    try:
        return services.checked_order(db, id, check)
    except Exception:
        raise


@order.post('/create_order', status_code=200)
async def create_order(
    *,
    db: Session = Depends(get_db),
    order_data: OrderSchema,
) -> None:
    """Create order."""
    return services.create_order(db=db, order_data=order_data)


@order.post('/update-payment-and-order-status', status_code=200)
def order_status() -> None:
    """Order status."""
    db = get_session()
    orders = db.query(OrderDB).filter(OrderDB.id.isnot(None))
    for order in orders:
        return {
            'order_id': order.id,
            'payment_id': order.payment_id,
            'order_status': order.order_status,
        }
    return None


def check_status_pedding() -> None:
    """Check status pedding."""
    data = order_status()
    logger.debug(data)
    if data.get('order_status') == 'pending':
        return 'pending'
    return None


def status_pending() -> None:
    """Status pending."""
    data = order_status()
    logger.debug(data)
    db = get_session()
    payment = db.query(PaymentDB).filter_by(id=data.get('payment_id')).first()
    return return_transaction(payment.gateway_id)


def status_paid() -> None:
    """Status paid."""
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
    return None


def alternate_status(status: str) -> None:
    """Alternate status."""
    order_status = {'pending': status_pending, 'paid': status_paid}
    return order_status[status]
