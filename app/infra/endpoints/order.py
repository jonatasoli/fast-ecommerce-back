from fastapi import APIRouter, Depends, status
from fastapi.routing import get_websocket_app
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from app.infra.worker import task_message_bus

from app.infra.database import get_async_session, get_session
from constants import OrderStatus
from app.order import services
from app.infra.deps import get_db
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


@order.get(
    '/orders',
    summary="Get all orders",
    status_code=status.HTTP_200_OK,
     tags=["admin"],
 )
async def get_orders(
    page: int = 1,
    offset: int = 10,
    db: Session = Depends(get_session),
):
    """## [ADMIN] Get orders paid.

    - **date_initial** -> Optional determine start date period if empty return all
    - **date_final** -> Optional determine final date period if empty return all
    - **status** -> Optional filter orders by status
    - **user_id** -> Optional filter by user_id
    """
    try:
        return services.get_orders(page, offset, db=db)
    except Exception:
        raise
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


@order.put(
    '/tracking_number/{order_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def tracking_number(
    order_id: int,
    tracking: TrackingFullResponse,
    db: async_sessionmaker = Depends(get_async_session),
) -> None:
    """Put trancking number."""
    try:
        message = task_message_bus
        return await services.put_tracking_number(
            order_id,
            data=tracking,
            db=db,
            message=message,
        )
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
def order_status(db: sessionmaker = Depends(get_session)) -> dict:
    """Order status."""
    with db() as session:
        orders = session.scalars(
            select(OrderDB).where(OrderDB.order_id.isnot(None)),
        )
        for order in orders.all():
            return {
                'order_id': order.id,
                'payment_id': order.payment_id,
                'order_status': order.order_status,
            }
    return {}


def check_status_pedding() -> str:
    """Check status pedding."""
    data = order_status()
    logger.debug(data)
    if data.get('order_status') == 'pending':
        return 'pending'
    return ''


def status_pending() -> None:
    """Status pending."""
    data = order_status()
    logger.debug(data)
    db = get_session()
    _ = db.query(PaymentDB).filter_by(id=data.get('payment_id')).first()
    # TODO create return payment from payment gateway


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
