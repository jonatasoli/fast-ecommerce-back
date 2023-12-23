from sqlalchemy import Select
from sqlalchemy.orm import Session, sessionmaker

from app.infra.models import SalesCommissionDB
from app.report.entities import Commission, UserSalesComissions


def create_sales_commission(
    sales_commission: Commission, db: sessionmaker
) -> SalesCommissionDB:
    with db.begin() as session:
        commission = SalesCommissionDB(**sales_commission.model_dump())
        session.add(commission)
        session.flush()
        return commission


async def get_user_sales_comissions(
    user, paid: bool, released: bool, db: Session
):
    async with db.begin() as session:
        query = (
            Select(SalesCommissionDB)
            .filter(SalesCommissionDB.user_id == user.user_id)
            .filter(SalesCommissionDB.paid == paid)
            .filter(SalesCommissionDB.released == released)
        )
        comission = await session.execute(query)
        return UserSalesComissions(
            comissions=[
                Commission(
                    order_id=c.order_id,
                    user_id=c.user_id,
                    commission=c.commission,
                    date_created=c.date_created,
                    release_date=c.release_date,
                    released=c.released,
                    paid=c.paid,
                )
                for c in comission.scalars().all()
            ]
        )
