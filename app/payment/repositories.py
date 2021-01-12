from models.order import Product
from models.transaction import Transaction, Payment, CreditCardFeeConfig


class CreateProduct:
    def __init__(self, db, product, _upsell):
        self.db= db
        self.product = product
        self._upsell = _upsell


    def post_product(self):
        db_product = Product(
                name=self.product.name,
                price=self.product.price,
                direct_sales=self.product.direct_sales,
                upsell=self._upsell
                )
        self.db.add(db_product)
        self.db.commit()
        return db_product


class DecreaseProduct:
    def decrease_product():
        _product_decrease = db.query(Product).filter_by(id=item.get("id")).first()
        return _product_decrease


class CreatePayment:
    def __init__(self, user_id, _total_amount, _payment_method, _installments, db):
        self.user_id = user_id
        self._total_amount = _total_amount
        self._payment_method = _payment_method
        self._installments = _installments
        self.db = db


    def create_payment():
        db_payment = Payment(
                user_id=self.user_id,
                amount=int(self._total_amount)*100,
                status="pending",
                payment_method=self._payment_method,
                payment_gateway="PagarMe",
                installments=self._installments if self._installments else 1
                )
        self.db.add(db_payment)
        self.db.commit()
        return db_payment


class CreateTransaction:
    def __init__(self, user_id, cart, order, _affiliate, db_payment):
        self.user_id = user_id
        self.cart = cart 
        self.order = order 
        self._affiliate = _affiliate
        self.db_payment = db_payment


    def create_transaction(self):
        db_transaction = Transaction(
            user_id = self.user_id,
            amount= self.cart.get("amount"),
            order_id=self.order.id,
            qty= self.cart.get("qty"),
            payment_id=self.db_payment.id,
            status= "pending",
            product_id=self.cart.get("product_id"),
            affiliate= self._affiliate,
        )
        return db_transaction


class GetCreditCardConfig:
    def __init__(self, db, _product_id):
        self.db = db
        self._product_id = _product_id


    def get_config(self):
        _product_config = self.db.query(Product).filter_by(id=int(self._product_id)).first()

        _config_installments = self.db.query(CreditCardFeeConfig)\
            .filter_by(id=_product_config.installments_config)\
            .first()
        return _config_installments