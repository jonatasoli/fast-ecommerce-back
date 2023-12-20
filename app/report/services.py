from sqlalchemy.orm import sessionmaker

from fastapi import Depends
from sqlalchemy.orm import Session
from app.report.entities import Commission
from . import repository
from ..infra.models import SalesCommissionDB
from app.infra.database import get_session


def get_db():
    Session = get_session()
    return Session()


async def get_user_sales_comissions(user, paid: bool, db: Session):
    """Get user sales commissions."""
    ...


def create_sales_commission(
        sales_commission: Commission,
        db: Session = Depends(get_db),
) -> SalesCommissionDB:
    return repository.create_sales_commission(sales_commission, db)
