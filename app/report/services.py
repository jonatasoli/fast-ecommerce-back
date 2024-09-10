# ruff: noqa: ANN401 FBT001 B008
from typing import Any
from app.entities.product import ProductInDB
from sqlalchemy.orm import Session, sessionmaker

from app.infra.database import get_session
from app.entities.report import Commission, InformUserProduct
from app.report import repository
from app.product import repository as product_repository
from app.infra.models import SalesCommissionDB
from faststream.rabbit import RabbitQueue
from app.infra.worker import task_message_bus


async def get_user_sales_comissions(
    user: Any,
    paid: bool,
    released: bool,
    db: Session,
) -> list[Commission | None]:
    """Get user sales commissions."""
    async with db.begin() as transaction:
        return await repository.get_user_sales_comissions(
            user,
            paid=paid,
            released=released,
            transaction=transaction,
        )


def create_sales_commission(
    sales_commission: Commission,
    db: sessionmaker = get_session(),
) -> SalesCommissionDB:
    """Get sales commit at all."""
    with db.begin() as transaction:
        comission_db = repository.create_sales_commission(
            sales_commission,
            transaction=transaction,
    )
        transaction.commit()
    return comission_db


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
