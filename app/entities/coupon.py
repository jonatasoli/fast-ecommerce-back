from decimal import Decimal
from pydantic import BaseModel


class CouponBase(BaseModel):
    code: str
    discount: Decimal


class CouponCreate(CouponBase):
    active: bool = True
    qty: int = 1
    affiliate: int = None
