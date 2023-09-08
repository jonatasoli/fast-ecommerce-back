import abc
from decimal import Decimal
from typing import Self

from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.infra.constants import OrderStatus
from app.infra.models import order
from app.order.entities import OrderDBUpdate


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[order.Order]

    async def create_order(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> order.Order:
        """Create a new order."""
        return await self._create_order(cart, discount, affiliate)

    async def get_order_by_cart_uuid(self: Self, cart_uuid: str) -> order.Order | None:
        """Get an order by its cart uuid."""
        return await self._get_order_by_cart_uuid(cart_uuid)

    async def create_order_status_step(
        self: Self,
        order_id: int,
        status: str,
        sending: bool = False,
    ) -> int:
        """Create a new order status step."""
        return await self._create_order_status_step(order_id, status, sending)

    @abc.abstractmethod
    async def _create_order(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> order.Order:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_order_by_cart_uuid(self: Self, cart_uuid: str) -> order.Order | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _create_order_status_step(
        self: Self,
        order_id: int,
        status: str,
        sending: bool = False,
    ) -> int:
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
        import ipdb; ipdb.set_trace()
        async with self.session().begin() as session:
            order = order.Order(
                customer_id=cart.customer_id,
                cart_uuid=cart.uuid,
                discount=cart.discount,
                order_date=datetime.now(),
                order_status=OrderStatus.PAYMENT_PENDING.value,
                last_updated=datetime.now(),
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

    async def _get_order_by_cart_uuid(
            self: Self,
            cart_uuid: str) -> order.Order | None:
        """Get an order by its cart uuid."""
        async with self.session().begin() as session:
            order_query = select(order.Order).where(
                order.Order.cart_uuid == cart_uuid,
            )
            return await session.execute(order_query).scalar_one_or_none()

    async def _create_order_status_step(
        self: Self,
        order_id: int,
        status: str,
        sending: bool = False,
    ) -> int:
        """Create a new order status step."""
        async with self.session().begin() as session:
            order_status_step = order.OrderStatusStep(
                order_id=order_id,
                status=status,
                sending=sending,
                active=True,
                last_updated=datetime.now(),
            )
            session.add(order_status_step)
            session.commit()
        return order_status_step.id
