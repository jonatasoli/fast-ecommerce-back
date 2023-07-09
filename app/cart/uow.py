# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc
from decimal import Decimal
from typing import TypeVar
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.entities.product import ProductCart


from config import settings


Self = TypeVar('Self')


class AbstractUnitOfWork(abc.ABC):
    @abc.abstractmethod
    async def get_product_by_id(self: Self) -> ProductCart:
        """Must return a product by id."""
        ...


def get_engine() -> AsyncEngine:
    """Create a new engine."""
    return create_async_engine(
        settings.DATABASE_URI,
        pool_size=10,
        max_overflow=0,
        echo=True,
    )


def get_session() -> sessionmaker:
    """Create a new session."""
    return sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    async def __init__(
        self: Self,
        session_factory: sessionmaker = get_session(),  # noqa: B008
    ) -> None:
        self.session_factory = session_factory

    async def get(self: Self) -> None:
        async with self._session() as session, session.begin():
            await session.execute('SELECT 1')

    async def get_product_by_id(self: Self, product_id: int) -> ProductCart:
        ...


class MemoryUnitOfWork(AbstractUnitOfWork):
    async def get_product_by_id(self: Self, product_id: int) -> ProductCart:
        """Must add product to new cart and return cart."""

        async def create_product_cart() -> ProductCart:
            return ProductCart(
                product_id=product_id,
                quantity=10,
                price=Decimal('10.00'),
            )

        return await create_product_cart()
