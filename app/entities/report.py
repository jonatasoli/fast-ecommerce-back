from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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


class InformUserProduct(BaseModel):
    """Data to inform admin user product."""

    product_id: int
    phone: str
    email: str
