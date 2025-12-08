# ruff: noqa: I001
from pydantic import TypeAdapter
from app.coupons import repository

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.entities.coupon import CouponCreate, CouponInDB, CouponUpdate, CouponsResponse
from app.infra.database import get_async_session
from app.infra.models import CouponsDB
from app.user.services import verify_admin
from typing import Annotated, Any

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

coupon = APIRouter(
    prefix='/coupon',
    tags=['coupon', 'admin'],
)


@coupon.get(
    '/',
    summary='Get all coupons',
    status_code=status.HTTP_200_OK,
)
async def get_coupons(
    *,
    page: int = 1,
    offset: int = 10,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Any, Depends(get_async_session)],
):
    """Get all coupons."""
    await verify_admin(token, db=db)
    async with db() as transaction:
        return await repository.get_coupons(
            page=page,
            offset=offset,
            transaction=transaction,
        )


@coupon.get(
    '/{coupon_id}',
    summary='Get coupon',
    status_code=status.HTTP_200_OK,
)
async def get_coupon(
    coupon_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Get coupon."""
    await verify_admin(token, db=db)
    async with db() as transaction:
        return await repository.get_coupon(
            coupon_id=coupon_id,
            transaction=transaction,
        )


@coupon.post(
    '/',
    summary='Post coupon',
    status_code=status.HTTP_201_CREATED,
)
async def create_coupon(
    create_data: CouponCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Get coupon."""
    await verify_admin(token, db=db)
    async with db().begin() as transaction:
        coupon_db = CouponsDB(**create_data.model_dump())
        transaction.session.add(coupon_db)
        await transaction.commit()
    return coupon_db


@coupon.patch(
    '/{coupon_id}',
    summary='Update coupon',
    status_code=status.HTTP_200_OK,
)
async def update_coupon(
    coupon_id: int,
    data_update: CouponUpdate,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Update coupon."""
    await verify_admin(token, db=db)
    async with db() as transaction:
        return await repository.update_coupon(
            coupon_id=coupon_id,
            data_update=data_update,
            transaction=transaction,
        )


@coupon.delete(
    '/{coupon_id}',
    summary='Update coupon',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_coupon(
    coupon_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    db=Depends(get_async_session),
):
    """Update coupon."""
    await verify_admin(token, db=db)
    async with db() as transaction:
        return await repository.delete_coupon(
            coupon_id=coupon_id,
            transaction=transaction,
        )
