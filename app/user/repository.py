import enum
import math
from pydantic import TypeAdapter
from sqlalchemy import asc, func, select, update

from sqlalchemy.sql import desc
from app.entities.user import UserInDB, UsersDBResponse
from app.infra import models
from constants import Direction


class UsersOderByDB(enum.Enum):
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
    user_query = select(models.UserDB).where(models.UserDB.user_id == user_id)
    async with transaction:
        return await transaction.session.scalar(user_query)

async def get_user_by_username(
    username: str,
    *,
    transaction,
) -> models.UserDB | None:
    """Get an user by its username."""
    user_query = select(models.UserDB).where(
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
    search_document: str | None,
    search_name: str | None,
    order_by: str,
    direction: str,
    page: int,
    limit: int,
    transaction,
):
    """Select all users."""
    async with transaction:
        query_users = select(models.UserDB)
        if search_name:
            query_users = query_users.where(
                models.UserDB.name.like(search_name),
            )
        elif search_document:
            query_users = query_users.where(
                models.UserDB.document.like(search_document),
            )

        if order_by and direction == Direction.asc:
            query_users = query_users.order_by(
                asc(getattr(UsersOderByDB, order_by)),
            )
        else:
            query_users = query_users.order_by(desc(
                getattr(UsersOderByDB, order_by)),
            )

        total_records = await transaction.scalar(
            select(func.count(models.UserDB.user_id)),
        )
        if page > 1:
            query_users = query_users.offset((page - 1) * limit)
        query_users = query_users.limit(limit)

        users_db = await transaction.scalars(query_users)
        adapter = TypeAdapter(list[UserInDB])

    return UsersDBResponse(
        users=adapter.validate_python(users_db.all()),
        page=page,
        limit=limit,
        total_pages=math.ceil(total_records / limit) if total_records else 1,
        total_records=total_records if total_records else 0,
    )

