import abc
import math
from typing import Self

from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.entities.coupon import CouponInDB, CouponsResponse, CouponUpdate
from app.infra.models import CouponsDB


class Coupon: ...


class AbstractRepository(abc.ABC):
    """Abstract coupon repository."""

    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[Coupon]

    def add(self: Self, coupon: Coupon) -> Coupon:
        self._add(coupon)
        self.seen.add(coupon)

    def get(self: Self, coupon_name: str) -> Coupon:
        coupon = self._get(coupon_name)
        if coupon:
            self.seen.add(coupon)
        return coupon

    @abc.abstractmethod
    def _add(self: Self, coupon: Coupon) -> Coupon:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self: Self, coupon_name: str) -> Coupon:
        raise NotImplementedError


async def get_coupons(offset: int, page: int, transaction):
    """Get coupons."""
    async with transaction.begin():
        quantity_query = select(CouponsDB).options(
            joinedload(CouponsDB.user),
            joinedload(CouponsDB.product),
        )
        total_records = await transaction.scalar(
            select(func.count(CouponsDB.coupon_id)),
        )
        if page > 1:
            quantity_query = quantity_query.offset((page - 1) * offset)
        quantity_query = quantity_query.limit(offset)
        adapter = TypeAdapter(list[CouponInDB])
        coupons = await transaction.scalars(quantity_query)
        coupons = adapter.validate_python(coupons.unique().all())
        return CouponsResponse(
            page=page,
            offset=offset,
            total_records=total_records if total_records else 0,
            total_pages=math.ceil(total_records / offset) if total_records else 1,
            coupons=coupons,
        )


async def get_coupon(coupon_id, transaction):
    """Get coupons."""
    async with transaction.begin():
        quantity_query = (
            select(CouponsDB)
            .options(
                joinedload(CouponsDB.user),
                joinedload(CouponsDB.product),
            )
            .where(CouponsDB.coupon_id == coupon_id)
        )
        coupon = await transaction.scalar(quantity_query)
        return CouponInDB.model_validate(coupon)


async def update_coupon(coupon_id: int, data_update: CouponUpdate, transaction):
    """Update Coupon."""
    async with transaction.begin():
        quantity_query = (
            select(CouponsDB)
            .options(
                joinedload(CouponsDB.user),
                joinedload(CouponsDB.product),
            )
            .where(CouponsDB.coupon_id == coupon_id)
        )
        coupon = await transaction.scalar(quantity_query)

        update_data = data_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(coupon, field, value)
        transaction.add(coupon)
        await transaction.commit()

    return coupon


async def delete_coupon(coupon_id: int, transaction):
    """Delete Coupon."""
    async with transaction.begin():
        quantity_query = (
            select(CouponsDB)
            .options(
                joinedload(CouponsDB.user),
                joinedload(CouponsDB.product),
            )
            .where(CouponsDB.coupon_id == coupon_id)
        )
        coupons = await transaction.scalar(quantity_query)
        coupons.active = False
        transaction.add(coupons)
        await transaction.commit()
