from models.order import Order
from job_service.service import get_session
from sqlalchemy.orm import Session
from models.order import Order
from gateway.payment_gateway import return_transaction
from loguru import logger


db=get_session()
payment_id = []
status_pagarme = []
orders = db.query(Order).filter(~Order.order_status.in_(['paid', 'refused'])).all()


def order_status():
    cont = 0
    for status in orders:
        gateway_id = return_transaction(status.payment_id)
        db_order = db.query(Order).filter(Order.payment_id == status.payment_id).first()
        if db_order.payment_id == 0:
            db_order.order_status = 'refused'
        else:
            logger.debug(f"------- ID STATUS {status.payment_id}-----------")
            logger.debug(f"---- ID {gateway_id} ----")
            db_order.order_status = gateway_id.get('status')
        db.commit()
        cont += 1
    logger.debug(f"Foram processados {cont} pedidos")

def main():
    order_status()


if __name__ == "__main__":
    main()

