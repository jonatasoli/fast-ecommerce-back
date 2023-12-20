from app.infra.models import SalesCommissionDB
from sqlalchemy.orm import Session

from app.report.entities import Commission


def create_sales_commission(
    sales_commission: Commission, db: Session
) -> SalesCommissionDB:
    commission = SalesCommissionDB(**sales_commission.model_dump())
    db.add(commission)
    db.flush()
    return commission
