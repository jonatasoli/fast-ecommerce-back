from decimal import Decimal
from pydantic import BaseModel


class CouponBase(BaseModel):
    code: str
    coupon_fee: Decimal


class CouponCreate(CouponBase):
    active: bool = True
    qty: int = 1
    affiliate: int = None
