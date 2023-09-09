import abc
from typing import Self
from sqlalchemy import select, update

from sqlalchemy.orm import SessionTransaction, sessionmaker
from app.infra.models import users
from tests.factories_db import USER_ID_ROLE

class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[users.User]

    async def get_user_by_id(self: Self, user_id: int) -> users.User:
        return await self._get_user_by_id(user_id)

    async def get_user_by_username(self: Self, username: str) -> users.User:
        return await self._get_user_by_username(username)

    async def update_user(self: Self, user_id: int, user: users.User) -> users.User:
        return await self._update_user(user_id, user)

    @abc.abstractmethod
    async def _get_user_by_id(self: Self, user_id: int) -> users.User:
        """Get an user by its id."""
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_user_by_username(self: Self, username: str) -> users.User:
        """Get an user by its username."""
        raise NotImplementedError

    @abc.abstractmethod
    async def _update_user(self: Self, user_id: int, user: users.User) -> users.User:
        """Update an user."""
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, transaction: SessionTransaction) -> None:
        super().__init__()
        self.transaction = transaction

    async def _get_user_by_id(self: Self, user_id: int) -> users.User:
        """Get an user by its id."""
        user_query= select(users.User).where(users.User.user_id == user_id)
        user = await self.transaction.session.scalar(user_query)
        return user

    async def _get_user_by_username(self: Self, username: str) -> users.User | None:
        """Get an user by its username."""
        user_query= select(users.User).where(users.User.username == username)
        user = await self.transaction.session.scalar(user_query)
        return user

    async def _update_user(self: Self, user_id: int, user: users.User) -> users.User:
        """Update an user."""
        user_query = update(users.User).where(users.User.user_id == user_id).values(customer_id=user.customer_id)
        updated_user = await self.transaction.session.execute(user_query)
        await self.transaction.session.commit()
        return updated_user
