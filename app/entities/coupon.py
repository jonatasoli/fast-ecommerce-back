from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class CouponBase(BaseModel):
    code: str


class CouponCreate(CouponBase):
    active: bool = True
    qty: int = 1
    affiliate: int = None
    discount: Decimal


class CouponUpdate(CouponCreate):
    ...


class CouponResponse(CouponCreate):
    model_config = ConfigDict(from_attributes=True)
