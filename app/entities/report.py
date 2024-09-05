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


class UserSalesCommissions(BaseModel):
    commissions: list[Commission] | list


class InformUserProduct(BaseModel):
    """Data to inform admin user product."""

    product_id: int
    phone: str
    email: str


class InformUserProductInDB(BaseModel):
    """Data represents table inform_product_to_admin."""

    user_mail: str
    user_phone: str
    product_id: int
    product_name: str
