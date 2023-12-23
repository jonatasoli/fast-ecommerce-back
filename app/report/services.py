from sqlalchemy.orm import Session, sessionmaker

from app.infra.database import get_session
from app.report.entities import Commission
from . import repository
from ..infra.models import SalesCommissionDB


async def get_user_sales_comissions(
    user, paid: bool, released: bool, db: Session
):
    """Get user sales commissions."""
    return await repository.get_user_sales_comissions(
        user=user, paid=paid, released=released, db=db
    )


def create_sales_commission(
    sales_commission: Commission,
    db: sessionmaker = get_session(),
) -> SalesCommissionDB:
    return repository.create_sales_commission(sales_commission, db=db)
