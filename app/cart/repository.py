import abc
from typing import Any, TypeVar

from sqlalchemy import select

from models import order


Self = TypeVar('Self')


class ProductNotFoundError(Exception):
    """Raised when a product is not found in the repository."""

    ...


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Product]

    def get_product(self: Self, id: int) -> order.Product:   # noqa: A002
        return self._get_product(id)

    def get_product_inventory(self: Self, product_id: int) -> int:
        return self._get_inventory(product_id)

    @abc.abstractmethod
    def _get_product(self: Self, sku: str) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_inventory(self: Self, product_id: int) -> int:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: Any) -> None:   # noqa: ANN401
        super().__init__()
        self.session = session

    async def _get_product(
        self: Self,
        id: int,  # noqa: A002
    ) -> order.Product:
        """Queery must return a valid product in search by id."""
        async with self.session().begin() as session:
            product = await session.execute(
                select(order.Product).where(order.Product.id == id),
            )
            if not product:
                msg = f'No product with id {id}'
                raise ProductNotFoundError(msg)

            return product.fetchone()
