from datetime import datetime, timedelta
from decimal import Decimal

from loguru import logger

from app.report.entities import Commission
from app.infra.worker import task_message_bus
from app.report.services import create_sales_commission


@task_message_bus.event('sales_commission')
def task_create_sales_commission(
        user_id: int,
        order_id: int,
        commission_percentage: Decimal,
        subtotal: Decimal,
) -> None:
    logger.info(f'Creating sales commission for order {order_id}')
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
        )
    )
