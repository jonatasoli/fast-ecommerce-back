from datetime import datetime
from decimal import Decimal

from loguru import logger

from models.order import Order, OrderItems, Product
from models.transaction import CreditCardFeeConfig, Payment, Transaction
from payment.adapter import get_db
from payment.schema import (
    ConfigCreditCardResponse,
    OrderFullResponse,
)


def rollback():
    db = get_db()
    db.rollback()


class ProductDB:
    def __init__(self, item) -> None:
        self.db = get_db()
        self.item = item

    def decrease_product(self):
        with self.db:
            return (
                self.db.query(Product)
                .filter_by(id=self.item.get('id'))
                .first()
            )

    def add_product(self, _product_decrease):
        with self.db:
            self.db.add(_product_decrease)
            self.db.commit()


class OrderDB:
    def __init__(self, user_id) -> None:
        self.user_id = user_id

    def create_order(self):
        db = get_db()
        with db:
            db_order = Order(
                customer_id=self.user_id,
                order_date=datetime.now(),
                order_status='pending',
            )
            db.add(db_order)
            db.commit()
        return OrderFullResponse.from_orm(db_order)

    def create_order_items(self, db_order, cart):
        db = get_db()
        with db:
            db_item = OrderItems(
                order_id=db_order,
                product_id=cart.get('product_id'),
                quantity=cart.get('qty'),
            )
            db.add(db_item)
            db.commit()


class CreatePayment:
    def __init__(
        self, user_id, _payment_method, _installments, _total_amount
    ) -> None:
        self.user_id = user_id
        self._total_amount = _total_amount
        self._payment_method = _payment_method
        self._installments = _installments
        self.db = get_db()

    def create_payment(self):
        with self.db:
            db_payment = Payment(
                user_id=self.user_id,
                amount=int(self._total_amount) * 100,
                status='pending',
                payment_method=self._payment_method,
                payment_gateway='PagarMe',
                installments=self._installments if self._installments else 1,
            )
            self.db.add(db_payment)
            self.db.commit()
        return db_payment


class QueryPayment:
    def __init__(self, db) -> None:
        self.db = db

    def query(self):
        with self.db:
            return self.db.query(Payment).first()


class CreateTransaction:
    def __init__(self, user_id, cart, order, affiliate, payment_id) -> None:
        self.db = get_db()
        self.user_id = user_id
        self.cart = cart
        self.order = order
        self.affiliate = affiliate
        self.payment_id = payment_id

    def create_transaction(self):
        with self.db:
            db_transaction = Transaction(
                user_id=self.user_id,
                amount=self.cart.get('amount'),
                order_id=self.order.id,
                qty=self.cart.get('qty'),
                payment_id=self.payment_id,
                status='pending',
                product_id=self.cart.get('product_id'),
                affiliate=self.affiliate,
            )
            self.db.add(db_transaction)
            self.db.commit()


class GetCreditCardConfig:
    def __init__(self, _product_id) -> None:
        self.db = get_db()
        self._product_id = _product_id

    def get_config(self):
        with self.db:
            _product_config = (
                self.db.query(Product)
                .filter_by(id=int(self._product_id))
                .first()
            )

            _config_installments = (
                self.db.query(CreditCardFeeConfig)
                .filter_by(id=_product_config.installments_config)
                .first()
            )
            logger.debug(
                ConfigCreditCardResponse.from_orm(_config_installments),
            )
        return ConfigCreditCardResponse.from_orm(_config_installments)


class CreditCardConfig:
    def __init__(self, config_data) -> None:
        self.config_data = config_data

    def create_installment_config(self):
        return CreateCreditConfig(
            config_data=self.config_data,
        ).create_credit()


class CreateCreditConfig:
    def __init__(self, config_data) -> None:
        self.config_data = config_data

    def create_credit(self):
        db = get_db()
        _config = None
        with db:
            db_config = CreditCardFeeConfig(
                active_date=datetime.now(),
                fee=Decimal(self.config_data.fee),
                min_installment_with_fee=self.config_data.min_installment,
                mx_installments=self.config_data.max_installment,
            )
            db.add(db_config)
            db.commit()
            return ConfigCreditCardResponse.from_orm(db_config)


class UpdateStatus:
    def __init__(self, payment_data, order) -> None:
        self.payment_data = payment_data
        self.order = order

    def update_payment_status(self):
        try:
            db = get_db()
            with db:
                db_transaction = (
                    db.query(Transaction)
                    .filter_by(order_id=self.order.id)
                    .first()
                )

                db_transaction.status = self.payment_data.get('status')

                db_payment = (
                    db.query(Payment)
                    .filter_by(id=db_transaction.payment_id)
                    .first()
                )
                db_order = (
                    db.query(Order)
                    .filter_by(id=db_transaction.order_id)
                    .first()
                )
                db_payment.processed = True
                db_payment.processed_at = datetime.now()
                db_payment.gateway_id = self.payment_data.get('gateway_id')
                db_order.payment_id = self.payment_data.get('gateway_id')

                db_payment.token = self.payment_data.get('token')
                db_payment.authorization = self.payment_data.get(
                    'authorization_code',
                )
                db_payment.status = self.payment_data.get('status')
                db.add(db_transaction)
                db.add(db_payment)
                db.add(db_order)
                db.commit()
                db.refresh(db_transaction)
                db.refresh(db_payment)
                db.refresh(db_order)
        except Exception as e:
            logger.error(e)
            raise e
