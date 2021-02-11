from job_v2.repositories.orm_status import GetOrders, GetOrder
from ext.database import get_session
from models.order import Order
from gateway.payment_gateway import return_transaction
from loguru import logger


def get_db():
    SessionLocal = get_session()
    db = SessionLocal()
    return db


class ReturnGatewayID:
    def __init__(self, payment_id):
        self.payment_id = payment_id

    def gateway_id(self):
        gateway_id = return_transaction(self.payment_id)
        return gateway_id


class UpdateStatus:
    def __init__(self, order, gateway_id, db):
        self.order = order
        self.gateway_id = gateway_id
        self.db = db

    def update_status(self):
        if self.order.payment_id == 0:
            self.order.order_status = "refused"
        else:
            logger.debug(
                f"------- ID STATUS {self.gateway_id.get('gatewat_id')}-----------"
            )
            logger.debug(f"---- ID {self.gateway_id} ----")
            self.order.order_status = self.gateway_id.get("status")
        self.db.add(self.order)
        return self.order


class ForUpdate:
    def for_update(db=get_db()):
        cont = 0
        orders = GetOrders.get_orders()
        for status in orders:
            gateway_id = ReturnGatewayID(status.payment_id).gateway_id()
            order = GetOrder(status.payment_id, db).get_order()
            update = UpdateStatus(order, gateway_id, db).update_status()
            cont += 1
        db.commit()
        logger.debug(f"Foram processados {cont} pedidos")


def main():
    ForUpdate.for_update()


if __name__ == "__main__":
    main()
