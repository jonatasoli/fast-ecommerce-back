from sqlalchemy import select, update

from sqlalchemy.orm import SessionTransaction
from app.infra.models import users
from app.infra.models.transaction import Customer


async def get_user_by_id(
    user_id: int,
    *,
    transaction: SessionTransaction,
) -> users.User:
    """Get an user by its id."""
    user_query = select(users.User).where(users.User.user_id == user_id)
    return await transaction.session.scalar(user_query)


async def get_user_by_username(
    username: str,
    *,
    transaction: SessionTransaction,
) -> users.User | None:
    """Get an user by its username."""
    user_query = select(users.User).where(users.User.username == username)
    return await transaction.session.scalar(user_query)


async def update_user(
    user_id: int,
    *,
    user: users.User,
    transaction: SessionTransaction,
) -> users.User:
    """Update an user."""
    user_query = (
        update(users.User)
        .where(users.User.user_id == user_id)
        .values(customer_id=user.customer_id)
    )
    return await transaction.session.execute(user_query)
