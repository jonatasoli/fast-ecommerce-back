# ruff: noqa: ANN401 FBT001 B008
from typing import Any, List
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
) -> List[Commission | None]:
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
    with db.begin() as session:
        comission_db = repository.create_sales_commission(
            sales_commission,
            transaction=session,
    )
        session.commit()
    return comission_db
