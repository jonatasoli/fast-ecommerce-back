import abc
from decimal import Decimal
from typing import Self

from sqlalchemy.orm import sessionmaker

from sqlalchemy.sql import select

from app.entities.cart import CartPayment
from app.entities.payment import PaymentGateway, PaymentDBUpdate
from app.infra.constants import PaymentStatus
from app.infra.models import transaction


class AbstractRepository(abc.ABC):
    def __init__(self: Self) -> None:
        self.seen = set()  # type: Set[transaction.Payment]

    async def create_payment(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> transaction.Payment:
        """Create a new payment."""
        return await self._create_payment(cart, discount, affiliate)

    async def get_payment_by_order_id(
        self: Self,
        order_id: int,
    ) -> transaction.Payment | None:
        """Get an payment by its order id."""
        return await self._get_payment_by_order_id(order_id)

    async def update_payment(
        self: Self,
        payment_id: int,
        payment: PaymentDBUpdate,
    ) -> transaction.Payment:
        """Update an existing payment."""
        return await self._update_payment(payment_id, payment=payment)

    @abc.abstractmethod
    async def _create_payment(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> transaction.Payment:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_payment_by_order_id(
        self: Self,
        order_id: int,
    ) -> transaction.Payment | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _update_payment(
        self: Self,
        payment_id: int,
        payment: PaymentDBUpdate,
    ) -> transaction.Payment:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self: Self, session: sessionmaker) -> None:
        super().__init__()
        self.session = session

    async def _create_payment(
        self: Self,
        cart: CartPayment,
        discount: Decimal,
        affiliate: str | None,
    ) -> transaction.Payment:
        """Create a new order."""
        async with self.session().begin() as session:
            order = transaction.Payment(
                user_id=user_id,
                amount=cart.subtotal,
                token=cart.payment_intent_id,
                gateway_id=1,
                status=PaymentStatus.PENDING,
                authorization=cart.payment_intent_id,
                payment_method=cart.payment_method_id,
                payment_gateway=PaymentGateway.STRIPE.value,
                installments=cart.installments,
            )

            session.add(order)
            session.commit()
        return order

    async def _get_payment_by_id(
        self: Self,
        payment_id: int,
    ) -> transaction.Payment:
        """Get an payment by its id."""
        async with self.session().begin() as session:
            payment_query = select(transaction.Payment).where(
                transaction.Payment.payment_id == payment_id,
            )
            return await session.execute(payment_query).scalar_one()

    async def _update_payment(
        self: Self,
        payment_id: int,
        payment: PaymentDBUpdate,
    ) -> transaction.Payment:
        """Update an existing payment."""
        async with self.session().begin() as session:
            update_query = (
                self.session.update(transaction.Payment)
                .where(transaction.Payment.payment_id == payment_id)
                .values(
                    **payment.model_dump(
                        exclude_unset=True,
                    ),
                )
                .returning(transaction.Payment)
            )
            return self.session.execute(update_query)

    async def _get_payment_by_order_id(
        self: Self,
        order_id: int
    ) -> transaction.Payment | None:
        """Get payment by order id or return None if not exists."""
        async with self.session().begin() as session:
            payment_query = select(transaction.Payment).where(
                transaction.Payment.order_id == order_id,
            )
            return await session.execute(payment_query).scalar_one_or_none()
