import abc
from decimal import Decimal
from typing import Self

from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.infra.constants import OrderStatus
from app.infra.endpoints import order
from app.order.entities import OrderDBUpdate


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Product]

    async def create_order(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> order.Order:
        """Create a new order."""
        return await self._create_order(cart, discount, affiliate)

    @abc.abstractmethod
    async def _create_order(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> order.Order:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: sessionmaker) -> None:
        super().__init__()
        self.session = session

    async def _create_order(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> order.Order:
        """Create a new order."""
        async with self.session().begin() as session:
            order = order.Order(
                customer_id=cart.customer_id,
                order_date=datetime.now(),
                order_status=OrderStatus.PAYMENT_PENDING,
                last_updated=datetime.now(),
                discount=discount,
                affiliate=affiliate,
            )
            session.add(order)
            session.commit()
        return order

    async def _get_order_by_id(self: Self, order_id: int) -> order.Order:
        """Get an order by its id."""
        async with self.session().begin() as session:
            order_query = select(order.Order).where(
                order.Order.order_id == order_id,
            )
            return await session.execute(order_query).scalar_one()

    async def _update_order(self: Self, order: OrderDBUpdate) -> order.Order:
        """Update an existing order."""
        async with self.session().begin() as session:
            update_query = (
                self.session.update(order.Order)
                .where(order.Order.order_id == order.order_id)
                .values(
                    **order.model_dump(
                        exclude_unset=True,
                        exclude={'order_id'},
                    ),
                    last_updated=datetime.now(),
                )
                .returning(order.Order)
            )
            return self.session.execute(update_query)
