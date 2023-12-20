from fastapi import Depends
from sqlalchemy.orm import Session

from app.infra.database import get_session
from app.report.entities import Commission
from . import repository
from ..infra.models import SalesCommissionDB


async def get_user_sales_comissions(user, paid: bool, db: Session):
    """Get user sales commissions."""
    ...


def create_sales_commission(
    sales_commission: Commission,
    db: Session = get_session(),
) -> SalesCommissionDB:
    with db.begin() as session:
        return repository.create_sales_commission(sales_commission, session)
