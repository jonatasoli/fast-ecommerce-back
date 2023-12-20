from app.infra.models import SalesCommissionDB
from sqlalchemy.orm import Session

from app.report.entities import Commission


def create_sales_commission(
    sales_commission: Commission, db: Session
) -> SalesCommissionDB:
    with db as session:
        commission = SalesCommissionDB(**sales_commission.model_config)
        session.add(commission)
        session.flush()
        return commission
