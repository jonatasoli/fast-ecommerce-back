from datetime import datetime, UTC

from app.entities.product import ProductInDB
from app.entities.user import UserInDB
from app.infra.constants import Roles
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload, joinedload
from pydantic import TypeAdapter

from app.infra.models import (
    CoProducerFeeDB,
    FeeDB,
    InformUserProductDB,
    SalesCommissionDB,
    UserDB,
)
from app.entities.report import CommissionInDB, InformUserProduct, UserSalesCommissions


async def get_user_sales_commissions(
    user,
    *,
    paid: bool,
    released: bool,
    transaction: Session,
):
    """Get comission for user."""
    _ = released, paid
    query = (
        select(SalesCommissionDB)
        .where(
            SalesCommissionDB.user_id == user.user_id,
        )
    )
    commissions = await transaction.session.execute(query)
    adapter = TypeAdapter(list[CommissionInDB] | None)
    return UserSalesCommissions(
        commissions=adapter.validate_python(
            commissions.scalars().unique().all(),
        ),
    )


async def get_sales_commissions(
    *,
    paid: bool,
    released: bool,
    transaction: Session,
):
    """Get comission for user."""
    query = (
        select(SalesCommissionDB).options(
            joinedload(SalesCommissionDB.user),
        )
    )
    if paid:
        query = query.where(SalesCommissionDB.paid.is_(True))
    if released:
        query = query.where(SalesCommissionDB.released.is_(True))
    return await transaction.scalars(query)


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


async def update_payment_commissions(
    *,
    payment_id:int,
    paid_status: bool,
    db,
    cancelled_status: bool = False,
) -> None:
    """Update comission status."""
    async with db as transaction:
        query = select(SalesCommissionDB).where(
            SalesCommissionDB.payment_id == payment_id,
        )
        commission_db = await transaction.session.scalar(query)
        if commission_db:
            commission_db.paid = paid_status
            commission_db.active = True
            if cancelled_status:
                today = datetime.now(tz=UTC)
                commission_db.cancelled_at = cancelled_status
                commission_db.cancelled_at = today
                commission_db.paid = False
                commission_db.active = False
            transaction.session.add(commission_db)
            await transaction.session.commit()


async def get_admins(transaction):
    """Get list of admins."""
    async with transaction:
        query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(
            UserDB.role_id == Roles.ADMIN.value,
        )
        admin_db = await transaction.scalars(query)
        adapter = TypeAdapter(list[UserInDB])
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


def get_fees(transaction):
    """Get active fees."""
    query = select(FeeDB).where(FeeDB.active.is_(True))
    return transaction.scalars(query).all()

def get_coproducer(transaction):
    """Get co producers."""
    query = select(CoProducerFeeDB).where(CoProducerFeeDB.active.is_(True))
    return transaction.scalars(query).all()
