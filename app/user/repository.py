from sqlalchemy import select, update

from sqlalchemy.orm import SessionTransaction
from app.infra import models


async def get_user_by_id(
    user_id: int,
    *,
    transaction: SessionTransaction,
) -> models.UserDB:
    """Get an user by its id."""
    user_query = select(models.UserDB).where(models.UserDB.user_id == user_id)
    return await transaction.session.scalar(user_query)


async def get_user_by_username(
    username: str,
    *,
    transaction: SessionTransaction,
) -> models.UserDB | None:
    """Get an user by its username."""
    user_query = select(models.UserDB).where(
        models.UserDB.username == username,
    )
    return await transaction.session.scalar(user_query)


async def update_user(
    user_id: int,
    *,
    user: models.UserDB,
    transaction: SessionTransaction,
) -> models.UserDB:
    """Update an user."""
    user_query = (
        update(models.UserDB)
        .where(models.UserDB.user_id == user_id)
        .values(customer_id=user.customer_id)
    )
    return await transaction.session.execute(user_query)
