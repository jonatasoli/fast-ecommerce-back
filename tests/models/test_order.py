
from sqlalchemy import select

from constants import StepsOrder
from app.infra.models.order import Order, OrderStatusSteps
from tests.factories_db import (
    OrderFactory,
    OrderStatusStepsFactory,
    UserFactory,
)


def test_create_order(session):
    """Must create valid order."""
    # Arrange
    user = UserFactory()
    session.add(user)
    session.flush()
    new_order = OrderFactory(user=user)
    session.add(new_order)
    session.commit()

    # Act
    order = session.scalar(
        select(Order).where(Order.order_id == new_order.order_id),
    )

    # Assert
    assert order.order_id == 1
    assert order.order_status == StepsOrder.PAYMENT_PENDING.value
    assert order == new_order


def test_order_status_steps(session):
    """Must create valid order status steps."""
    # Arrange
    user = UserFactory()
    session.add(user)
    session.flush()
    order = OrderFactory(user=user)
    session.add(order)
    session.flush()
    new_order_status_steps = OrderStatusStepsFactory(order=order)
    session.add(new_order_status_steps)
    session.commit()

    # Act
    order_status_steps = session.scalar(
        select(OrderStatusSteps).where(
            OrderStatusSteps.order_id == new_order_status_steps.order_id,
        ),
    )

    # assert
    assert order_status_steps.order_id == 1
    assert order_status_steps == new_order_status_steps
