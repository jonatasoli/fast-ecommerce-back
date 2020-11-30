from models.order import Order
from job_service.service import get_session
from sqlalchemy.orm import Session
from models.order import Order
from gateway.payment_gateway import return_transaction


db=get_session()
payment_id = []
status_pagarme = []
orders = db.query(Order).filter(Order.order_status is not 'paid').all()


def query_order():
    for order in orders:
        _status = order.payment_id
        payment_id.append(_status)
        yield payment_id


def order_status():
    _status = query_order()
    cont = 0
    for status in _status:
        gateway_id = return_transaction(status[cont])
        db_order = db.query(Order).filter(Order.payment_id == status[cont]).first()
        db_order.order_status = gateway_id.get('status')
        db.commit()
        if len(status):
            cont += 1

def main():
    order_status()


if __name__ == "__main__":
    main()

