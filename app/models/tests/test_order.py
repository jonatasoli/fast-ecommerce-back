from models.order import OrderStatusSteps 
from datetime import datetime
from constants import StepsInvoice 


def test_order_status_steps(db):
    db_steps = OrderStatusSteps(
            order_id=1,
            status=StepsInvoice.PAYMENT_PENDING.value,
            last_updated=datetime.now(),
            sending=False,
            active=True
            )
    db.add(db_steps)
    db.commit()
    assert db_steps.id == 1

