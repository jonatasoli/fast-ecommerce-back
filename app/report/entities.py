from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SalesCommissionTaskValidate(BaseModel):
    order_id: int
    user_id: int
    commission_percentage: Decimal
    subtotal: Decimal


class Commission(BaseModel):
    order_id: int
    user_id: int
    commission: Decimal
    date_created: datetime
    release_date: datetime
    released: bool = False
    paid: bool = False
    model_config = ConfigDict(from_attributes=True)


class UserSalesComissions(BaseModel):
    comissions: list[Commission] | list[None]
