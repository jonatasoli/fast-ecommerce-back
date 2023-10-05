

from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.entities.user import Comission, UserSalesComissions


def get_user_sales_comissions(user, paid: bool, db: Session):
    """Get user sales commissions."""
    comissions = [Comission(
        order_id=1,
        user_name='Teste',
        commission=Decimal('10.00'),
        date_created=datetime.now(),
        released=True,
        paid=False,
    ),
        Comission(
        order_id=2,
        user_name='Teste',
        commission=Decimal('10.00'),
        date_created=datetime.now(),
        released=True,
        paid=True,
    ),
      ]
    user_comission = [comissions[1]] if paid else comissions
    return UserSalesComissions(comissions=user_comission)
