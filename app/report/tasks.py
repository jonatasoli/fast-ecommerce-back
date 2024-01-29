# ruff: noqa: DTZ005 B008 D103 ANN201 E501 D103 FBT001 ANN001 TID252 B008
from datetime import datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy.orm import sessionmaker

from app.infra.database import get_session
from app.infra.worker import task_message_bus
from app.report.entities import Commission
from app.report.repository import update_commissions
from app.report.services import create_sales_commission


@task_message_bus.event('sales_commission')
def task_create_sales_commission(
    user_id: int,
    order_id: int,
    subtotal: Decimal,
    coupon_id: int,
    commission_percentage: Decimal | None = None,
) -> None:
    logger.info(f'Creating sales commission for order {order_id}')
    if not commission_percentage:
        logger.error(
            f'Commission percentage is zero or not set for Coupon {coupon_id=} and order {order_id=}',
        )
        return
    today = datetime.now()
    release_data = today + timedelta(days=30)
    commission_value = Decimal(subtotal) * Decimal(commission_percentage)
    create_sales_commission(
        Commission(
            order_id=order_id,
            user_id=user_id,
            commission=commission_value,
            date_created=today,
            release_date=release_data,
        ),
    )


def update_sales_commission(db: sessionmaker = get_session()):
    date_threshold = datetime.now() - timedelta(days=30)
    update_commissions(date_threshold, db)
