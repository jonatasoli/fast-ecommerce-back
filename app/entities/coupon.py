from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class CouponNotFoundError(Exception):
    """Coupon not exist in database."""


class CouponBase(BaseModel):
    code: str
    model_config = ConfigDict(from_attributes=True)


class CouponCreate(CouponBase):
    active: bool = True
    qty: int = 1
    affiliate_id: int | None = None
    discount: Decimal
    commission_percentage: Decimal | None = None


class CouponUpdate(CouponCreate):
    ...


class CouponResponse(CouponCreate):
    coupon_id: int
    model_config = ConfigDict(from_attributes=True)
