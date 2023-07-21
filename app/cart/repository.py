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

    async def get_product_by_id(self: Self, product_id: int) -> order.Product:
        return await self._get_product_by_id(product_id)

    async def get_product_by_sku(
        self: Self,
        sku: str,
    ) -> order.Product:
        product = await self._get_product_by_sku(sku)
        self.seen.add(product)
        return product

    def get_products(self: Self, products: list) -> order.Product:
        return self._get_products(products)

    @abc.abstractmethod
    def _get_product_by_sku(
        self: Self,
        sku: str,
    ) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_product_by_id(self: Self, product_id: int) -> order.Product:
        raise NotImplementedError

    @abc.abstractmethod
    def _get_products(self: Self, products: list) -> order.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: Any) -> None:   # noqa: ANN401
        super().__init__()
        self.session = session

    async def _get_product_by_sku(
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

    async def _get_product_by_id(self: Self, product_id: int) -> order.Product:
        """Must return a product by id."""
        async with self.session() as session:
            product = await session.execute(
                select(order.Product).where(order.Product.id == product_id),
            )
            if not product:
                msg = f'No product with id {product_id}'
                raise ProductNotFoundError(msg)

            return product.scalars().first()

    async def _get_products(
        self: Self,
        products: list[int],
    ) -> list[order.Product]:
        """Must return updated products in db."""
        try:
            async with self.session() as session:
                products_db = await session.execute(
                    select(order.Product).where(
                        order.Product.id.in_(products),
                    ),
                )
                if not products_db:
                    msg = f'No products with ids {products}'
                    raise ProductNotFoundError(msg)

                return products_db.scalars().all()
        except Exception as e:
            raise e
