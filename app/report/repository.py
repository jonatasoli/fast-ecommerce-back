from datetime import datetime
from typing import List

from sqlalchemy import select, and_
from sqlalchemy.orm import Session, sessionmaker
from pydantic import TypeAdapter

from app.infra.models import SalesCommissionDB
from app.entities.report import Commission, UserSalesCommissions


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


def update_commissions(date_threshold: datetime, db: sessionmaker) -> None:
    """Update comission status."""
    with db.begin() as session:
        query = session.query(SalesCommissionDB).where(
            and_(
                SalesCommissionDB.date_created <= date_threshold,
                SalesCommissionDB.paid.is_(False),
            ),
        )
        query.update({SalesCommissionDB.paid: True})
        session.commit()
