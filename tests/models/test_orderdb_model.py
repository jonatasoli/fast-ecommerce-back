from sqlalchemy import select

from app.infra.constants import StepsOrder
from app.infra.models import OrderDB, OrderStatusStepsDB
from tests.factories_db import (
    OrderFactory,
    OrderStatusStepsFactory,
    UserDBFactory,
)


def test_create_order(session):
    """Must create valid order."""
    # Arrange
    user = UserDBFactory()
    session.add(user)
    session.flush()
    new_order = OrderFactory(user=user)
    session.add(new_order)
    session.commit()

    # Act
    order = session.scalar(
        select(OrderDB).where(OrderDB.order_id == new_order.order_id),
    )

    # Assert
    assert order.order_id == 1
    assert order.order_status == StepsOrder.PAYMENT_PENDING.value
    assert order == new_order


def test_order_status_steps(session):
    """Must create valid order status steps."""
    # Arrange
    user = UserDBFactory()
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
        select(OrderStatusStepsDB).where(
            OrderStatusStepsDB.order_id == new_order_status_steps.order_id,
        ),
    )

    # assert
    assert order_status_steps.order_id == 1
    assert order_status_steps == new_order_status_steps
