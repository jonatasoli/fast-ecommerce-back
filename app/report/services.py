# ruff: noqa: ANN401 FBT001 B008
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from typing import Any
from app.entities.product import ProductInDB
from app.infra.constants import FeeType
from sqlalchemy.orm import sessionmaker

from app.infra.database import get_session
from app.entities.report import CommissionInDB, InformUserProduct
from app.report import repository
from app.product import repository as product_repository
from app.infra.models import SalesCommissionDB
from faststream.rabbit import RabbitQueue
from app.infra.worker import task_message_bus


async def get_user_sales_comissions(
    user: Any,
    paid: bool,
    released: bool,
    db,
) -> list[CommissionInDB | None]:
    """Get user sales commissions."""
    async with db.begin() as transaction:
        return await repository.get_user_sales_comissions(
            user,
            paid=paid,
            released=released,
            transaction=transaction,
        )


def create_sales_commission( # noqa: PLR0913
    order_id: int,
    user_id: int,
    subtotal: Decimal,
    commission_percentage: Decimal | None,
    payment_id: int,
    db: sessionmaker = get_session(),
) -> SalesCommissionDB:
    """Get sales commit at all."""
    with db.begin() as transaction:
        fees = repository.get_fees(transaction)
        total_with_fees = subtotal
        for fee in fees:
            if fee.fee_type == FeeType.PERCENTAGE:
                total_with_fees -= total_with_fees * fee.value
            if fee.fee_type == FeeType.FIXED:
                total_with_fees -= fee.value

        co_producers_fee = repository.get_coproducer(transaction)
        if co_producers_fee:
            for co_producer_fee in co_producers_fee:
                total_with_fees -= total_with_fees * (co_producer_fee.percentage / 100)

        if not commission_percentage:
            raise ValueError('Error with percentage in report') #noqa: EM101 TRY003

        free_freight = 700
        freight_tax = 65
        if subtotal > free_freight:
            total_with_fees = total_with_fees - freight_tax
        commission_value = total_with_fees * commission_percentage
        today = datetime.now(tz=UTC)
        release_data = today + timedelta(days=30)

        commission_db = SalesCommissionDB(
                order_id=order_id,
                user_id=user_id,
                commission=commission_value,
                date_created=today,
                release_date=release_data,
                payment_id=payment_id,
        )
        transaction.add(commission_db)
        transaction.commit()
    return commission_db


async def notify_product_to_admin(
    *,
    inform: InformUserProduct,
    db,
    broker: RabbitQueue = task_message_bus,

):
    """Get user, product info and send notification to admin."""
    async with db.begin() as transaction:
        admins = await repository.get_admins(
            transaction=transaction,
        )
        product_db = await product_repository.get_product_by_id(
            inform.product_id,
            transaction=transaction,
        )
        product = ProductInDB.model_validate(product_db)
        inform_db = await repository.save_user_inform(
            inform=inform,
            product=product,
            transaction=transaction,
        )
        transaction.commit()

        await broker.publish(
            {
            'admin_email': admins,
            'product_id': inform_db.product_id,
            'product_name': inform_db.product_name,
            'user_email': inform_db.user_mail,
            'user_phone': inform_db.user_phone,
        },
        queue=RabbitQueue('inform_product_to_admin'),
        )
