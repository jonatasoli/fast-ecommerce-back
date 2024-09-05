from datetime import datetime
from typing import List

from app.entities.product import ProductInDB
from app.entities.user import UserInDB
from app.infra.constants import Roles
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from pydantic import TypeAdapter

from app.infra.models import InformUserProductDB, SalesCommissionDB, UserDB
from app.entities.report import Commission, InformUserProduct, UserSalesCommissions


def create_sales_commission(
    sales_commission: Commission,
    transaction,
) -> SalesCommissionDB:
    """Save commission in database."""
    with transaction:
        commission = SalesCommissionDB(**sales_commission.model_dump())
        transaction.add(commission)
        transaction.flush()
    return commission


async def get_user_sales_comissions(
    user,
    *,
    paid: bool,
    released: bool,
    transaction: Session,
):
    """Get comission for user."""
    query = (
        select(SalesCommissionDB)
        .where(
            SalesCommissionDB.user_id == user.user_id,
            SalesCommissionDB.paid == paid,
            SalesCommissionDB.released == released,
        )
    )
    commissions = await transaction.session.execute(query)
    adapter = TypeAdapter(List[Commission])
    return UserSalesCommissions(
        commissions=adapter.validate_python(commissions.scalars().all()),
    )


def update_commissions(date_threshold: datetime, db) -> None:
    """Update comission status."""
    with db.begin() as transaction:
        query = select(SalesCommissionDB).where(
            and_(
                SalesCommissionDB.date_created <= date_threshold,
                SalesCommissionDB.paid.is_(False),
            ),
        )
        commission_db = transaction.scalar(query)
        commission_db.paid = True
        transaction.add(commission_db)
        transaction.commit()


async def get_admins(transaction):
    """Get list of admins."""
    async with transaction:
        query = select(UserDB).where(UserDB.role_id == Roles.ADMIN.value)
        admin_db = await transaction.scalars(query)
        adapter = TypeAdapter(List[UserInDB])
        return adapter.validate_python(admin_db)


async def save_user_inform(
    *,
    inform: InformUserProduct,
    product: ProductInDB,
    transaction,
) -> InformUserProductDB:
    """Save product to notificate admin table."""
    async with transaction:
        inform_db = InformUserProductDB(
            user_mail=inform.email,
            user_phone=inform.phone,
            product_id=product.product_id,
            product_name=product.product_name,
        )
        transaction.add(inform_db)
    return inform_db

