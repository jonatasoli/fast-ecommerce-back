from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class CouponNotFoundError(Exception):
    """Coupon not exist in database."""


class CouponDontMatchWithUserError(Exception):
    """Coupon don't match with user code."""


class CouponBase(BaseModel):
    code: str
    model_config = ConfigDict(from_attributes=True)


class CouponCreate(CouponBase):
    active: bool = True
    qty: int = 1
    affiliate_id: int | None = None
    discount: Decimal
    discount_price: Decimal | None = None
    limit_price: Decimal | None = None


class CouponUpdate(CouponCreate):
    ...


class CouponResponse(CouponCreate):
    coupon_id: int
    commission_percentage: Decimal = Decimal(0)
    model_config = ConfigDict(from_attributes=True)
