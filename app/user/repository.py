import enum
import math
from pydantic import TypeAdapter
from sqlalchemy import asc, func, select, update

from sqlalchemy.orm import selectinload
from sqlalchemy.sql import desc
from app.entities.user import UserFilters, UserInDB, UsersDBResponse
from app.infra import models
from app.infra.constants import Direction


class UsersOderByDB(enum.Enum):
    string_name = models.UserDB.name
    user_id = models.UserDB.user_id
    username = models.UserDB.username
    mail = models.UserDB.email
    document = models.UserDB.document
    phone = models.UserDB.phone


async def get_user_by_id(
    user_id: int,
    *,
    transaction,
) -> models.UserDB:
    """Get an user by its id."""
    user_query = select(models.UserDB).options(
        selectinload(models.UserDB.addresses),
    ).where(models.UserDB.user_id == user_id)
    return await transaction.session.scalar(user_query)

async def get_user_by_username(
    username: str,
    *,
    transaction,
) -> models.UserDB | None:
    """Get an user by its username."""
    user_query = select(models.UserDB).options(
        selectinload(models.UserDB.addresses),
    ).where(
        models.UserDB.username == username,
    )
    async with transaction:
        return await transaction.session.scalar(user_query)


async def update_user(
    user_id: int,
    *,
    user: models.UserDB,
    transaction,
) -> models.UserDB:
    """Update an user."""
    user_query = (
        update(models.UserDB)
        .where(models.UserDB.user_id == user_id)
        .values(customer_id=user.customer_id)
    )
    async with transaction:
        return await transaction.session.execute(user_query)

async def get_users(
    *,
    filters: UserFilters,
    transaction,
):
    """Select all users."""
    query_users = select(models.UserDB).options(
        selectinload(models.UserDB.addresses),
    )
    if filters.search_name:
        query_users = query_users.where(
            models.UserDB.name.like(f'%{filters.search_name}'),
        )
    elif filters.search_document:
        query_users = query_users.where(
            models.UserDB.document.like(f'%{filters.search_document}%'),
        )

    if filters.order_by and filters.direction == Direction.asc:
        query_users = query_users.order_by(
            asc(getattr(UsersOderByDB, filters.order_by)),
        )
    else:
        query_users = query_users.order_by(desc(
            getattr(UsersOderByDB, filters.order_by)),
        )

    total_records = await transaction.session.scalar(
        select(func.count(models.UserDB.user_id)),
    )
    if filters.page > 1:
        query_users = query_users.offset((filters.page - 1) * filters.limit)
    query_users = query_users.limit(filters.limit)

    users_db = await transaction.session.scalars(query_users)
    adapter = TypeAdapter(list[UserInDB])

    return UsersDBResponse(
        users=adapter.validate_python(users_db),
        page=filters.page,
        limit=filters.limit,
        total_pages=math.ceil(total_records / filters.limit) if total_records else 1,
        total_records=total_records if total_records else 0,
    )

