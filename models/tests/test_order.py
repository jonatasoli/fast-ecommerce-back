from datetime import datetime

from constants import StepsOrder
from models.order import OrderStatusSteps


def test_order_status_steps(db_models):
    db_steps = OrderStatusSteps(
        order_id=1,
        status=StepsOrder.PAYMENT_PENDING.value,
        last_updated=datetime.now(),
        sending=False,
        active=True,
    )
    db_models.add(db_steps)
    db_models.commit()
    assert db_steps.id == 1
