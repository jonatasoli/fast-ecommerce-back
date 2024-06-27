# ruff: noqa: ANN401 FBT001 B008
from typing import Any
from sqlalchemy.orm import Session, sessionmaker

from app.infra.database import get_session
from app.entities.report import Commission
from app.report import repository
from app.infra.models import SalesCommissionDB


async def get_user_sales_comissions(
    user: Any,
    paid: bool,
    released: bool,
    db: Session,
) -> SalesCommissionDB:
    """Get user sales commissions."""
    return await repository.get_user_sales_comissions(
        user=user,
        paid=paid,
        released=released,
        db=db,
    )


def create_sales_commission(
    sales_commission: Commission,
    db: sessionmaker = get_session(),
) -> SalesCommissionDB:
    """Get sales commit at all."""
    return repository.create_sales_commission(sales_commission, db=db)
