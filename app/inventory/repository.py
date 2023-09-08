
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from app.infra.constants import InventoryOperation
from app.infra.models import order



import abc
from typing import Self


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Inventory]

    async def increase_inventory(
        self: Self,
        product_id: int,
        quantity: int,
    ) -> order.Inventory:
        """Increase inventory."""
        return await self._increase_inventory(product_id, quantity)

    async def decrease_inventory(
        self: Self,
        product_id: int,
        quantity: int,
    ) -> order.Inventory:
        """Decrease inventory."""
        return await self._decrease_inventory(product_id, quantity)

    async def total_inventory(
        self: Self,
        product_id: int,
    ) -> order.Inventory:
        """Get total inventory."""
        return await self._total_inventory(product_id)

    async def commit(
        self: Self,
    ) -> None:
        """Commit."""
        await self._commit()

    @abc.abstractmethod
    async def _increase_inventory(
        self: Self,
        product_id: int,
        quantity: int,
    ) -> order.Inventory:
        raise NotImplementedError

    @abc.abstractmethod
    async def _decrease_inventory(
        self: Self,
        product_id: int,
        quantity: int,
    ) -> order.Inventory:
        raise NotImplementedError

    @abc.abstractmethod
    async def _total_inventory(
        self: Self,
        product_id: int,
    ) -> order.Inventory:
        raise NotImplementedError

    @abc.abstractmethod
    async def _commit(
        self: Self,
    ) -> None:
        raise NotImplementedError



class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: sessionmaker) -> None:
        super().__init__()
        self.session = session

    async def _increase_inventory( self: Self,
        product_id: int,
        quantity: int,
    ) -> order.Inventory:
        """Increase inventory."""
        async with self.session() as session:
            inventory = order.Inventory(
                product_id=product_id,
                quantity=quantity,
                operation=InventoryOperation.INCREASE,
            )
            session.add(inventory)
            await session.commit()
            return inventory

    async def _total_inventory(self: Self, product_id: int) -> order.Inventory:
        """Get total inventory by product_id."""
        async with self.session() as session:
            products_query = select(order.Inventory).where(order.Inventory.product_id == product_id)
            products = await session.execute(products_query)
            total = products.scalar(func.sum('quantity'))
            return total

    async def _decrease_inventory(
            self: Self,
            product_id: int,
            quantity: int
    ) -> order.Inventory:
        """Decrease product in stock."""
        async with self.session() as session:
            inventory = order.Inventory(
                product_id=product_id,
                quantity=quantity,
                operation=InventoryOperation.DECREASE,
            )
            session.add(inventory)
            await session.flush()
            return inventory

    async def _commit(
        self: Self,
    ) -> None:
        """Commit."""
        await self.session.commit()

