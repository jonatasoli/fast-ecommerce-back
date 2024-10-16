from fastapi import APIRouter, Depends, status
from fastapi.routing import get_websocket_app
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from app.entities.user import UserNotAdminError
from app.infra.worker import task_message_bus

from app.infra.database import get_async_session, get_session
from app.user.services import get_admin, verify_admin
from app.infra.constants import OrderStatus
from app.order import services
from app.infra.deps import get_db
from app.infra.models import PaymentDB, OrderDB
from app.entities.order import (
    CancelOrder,
    OrderSchema,
    TrackingFullResponse,
    OrderUserListResponse,
    OrderFullResponse,
    OrderInDB,
)
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

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

@order.get('/user/{user_id}', status_code=200)
async def get_user_order(
    *,
    db: Session = Depends(get_db),
    user_id: int,
) -> list[OrderUserListResponse]:
    """Get order."""
    try:
        return services.get_user_order(db, user_id)
    except Exception as e:
        logger.error(e)
        raise

@order.get('/{order_id}', status_code=200)
async def get_order(
    *,
    db: Session = Depends(get_db),
    order_id: int,
) -> OrderInDB:
    """Get order."""
    try:
        return services.get_order(db, order_id)
    except Exception as e:
        logger.error(e)
        raise


@order.get('/user/{user_id}', status_code=200)
async def get_order_users_id(
    *,
    db: Session = Depends(get_db),
    user_id,
):
    """Get order users id."""
    try:
        return services.get_order_users(db, user_id)
    except Exception:
        raise


@order.patch('/{order_id}', status_code=status.HTTP_204_NO_CONTENT)
async def patch_order(
    *,
    order_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Patch order."""


@order.put('/{order_id}', status_code=status.HTTP_204_NO_CONTENT)
async def complete_order(
    order_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_async_session),
) -> None:
    """Patch order."""
    await verify_admin(token, db=db)
    try:
        return await services.complete_order(order_id,db=db)
    except Exception:
        raise


@order.delete('/{order_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    *,
    db: Session = Depends(get_db),
    cancel_reason: CancelOrder,
    order_id: int,
) -> None:
    """Delete order."""
    services.delete_order(order_id, cancel=cancel_reason, db=db)


@order.patch(
    '/{order_id}/tracking_number',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def tracking_number(
    order_id: int,
    tracking: TrackingFullResponse,
    token: str = Depends(oauth2_scheme),
    db: async_sessionmaker = Depends(get_async_session),
) -> None:
    """Patch trancking number."""
    _ = token
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
async def post_trancking_number(
    id: int,
    check: bool,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db),
) -> int:
    """Post trancking number."""
    with db() as session:
        if not (_ := get_admin(token, db=session)):
            raise UserNotAdminError
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
