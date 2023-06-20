from ext.database import get_session
from models.order import Order


class GetOrders:
    def get_orders(db=get_session()):
        orders = (
            db.query(Order)
            .filter(~Order.order_status.in_(['paid', 'refused']))
            .all()
        )
        return orders


class GetOrder:
    def __init__(self, payment_id):
        self.payment_id = payment_id
        self.db = db

    def get_order(self):
        order = (
            self.db.query(Order)
            .filter(Order.payment_id == self.gateway_id)
            .first()
        )
        db.add(order)
        return order
