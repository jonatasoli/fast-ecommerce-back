from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from dynaconf import settings
from domains.domain_user import (
    register_payment_address,
    register_shipping_address,
)
from payment.repositories import (
    ProductDB,
    GetCreditCardConfig,
    CreateTransaction,
    CreatePayment,
    UpdateStatus,
    OrderDB,
    rollback,
)
from payment.adapter import AdapterUser
from payment.schema import (
    CheckoutSchema,
    CreditCardPayment,
    SlipPayment,
    PaymentResponse,
)
from payment.gateway import credit_card_payment, slip_payment
from loguru import logger


class User:
    def __init__(self, db: Session, checkout_data: CheckoutSchema):
        self.db = db
        self.checkout_data = checkout_data
        self._user_email = checkout_data.get("mail")
        self._password = checkout_data.get("password")
        self._name = checkout_data.get("name")
        self._document = checkout_data.get("document")
        self._phone = checkout_data.get("phone")

    def user(self):
        _user = AdapterUser(
            db=self.db,
            _user_email=self._user_email,
            _password=self._password,
            _name=self._name,
            _document=self._document,
            _phone=self._phone,
        ).check_user()
        return _user


class Product:
    def __init__(self, item):
        self.item = item

    def decrease(self):
        _product = ProductDB(item=self.item)
        _product_decrease = _product.decrease_product()
        logger.debug(_product_decrease.quantity)
        _qty_decrease = int(self.item.get("quantity"))
        _product_decrease.quantity -= _qty_decrease
        if _product_decrease.quantity < 0:
            raise TypeError("Produto esgotado")
        else:
            _product.add_product(_product_decrease)


class ShoppingCart:
    def __init__(self, checkout_data: CheckoutSchema, user):
        self.checkout_data = checkout_data
        self.user = user
        self._shopping_cart = self.checkout_data.get("shopping_cart")

    def add_items(self):
        _items = []
        for cart in self._shopping_cart[0].get("itens"):
            logger.debug(cart)
            _items.append(
                {
                    "id": str(cart.get("product_id")),
                    "title": cart.get("product_name"),
                    "unit_price": cart.get("amount"),
                    "quantity": cart.get("qty"),
                    "tangible": str(cart.get("tangible")),
                }
            )
            for item in _items:
                Product(item=item).decrease()
            return _items

    def installments(self):
        _total_amount = Decimal(self._shopping_cart[0].get("total_amount"))
        _installments = self.checkout_data.get("installments")
        _config_installments = GetCreditCardConfig(
            self.checkout_data["shopping_cart"][0]["itens"][0]["product_id"]
        ).get_config()
        if _installments:
            _installments = int(_installments)
        else:
            _installments = 1
        if _installments > 12:
            raise TypeError("O número máximo de parcelas é 12")
        elif _installments >= _config_installments.min_installment_with_fee:
            _total_amount = _total_amount * (
                (1 + Decimal(_config_installments.fee)) ** _installments
            )
        return _installments


class ProcessPayment:
    def __init__(
        self,
        checkout_data: CheckoutSchema,
        user,
        affiliate,
        _customer,
        _billing,
        _shipping,
    ):
        self.checkout_data = checkout_data
        self.user = user
        self.affiliate = affiliate
        self.shopping_cart = ShoppingCart(
            checkout_data=self.checkout_data, user=self.user
        )
        self._installments = self.shopping_cart.installments()
        self._items = self.shopping_cart.add_items()
        self._customer = _customer
        self._billing = _billing
        self._shipping = _shipping

    def db_payment(self):
        db_payment = CreatePayment(
            user_id=self.user.id,
            _installments=self._installments,
            _payment_method=self.checkout_data.get("payment_method"),
        ).create_payment()
        return db_payment

    def process_payment(self):
        _db_payment = self.db_payment()
        if self.checkout_data.get("payment_method") == "credit-card":
            return self.payment_credit_card(_db_payment)
        else:
            return self.payment_slip(_db_payment)

    def payment_credit_card(self, db_payment):
        try:
            _payment = CreditCardPayment(
                api_key=settings.GATEWAY_API,
                amount=db_payment.amount,
                card_number=self.checkout_data.get("credit_card_number"),
                card_cvv=self.checkout_data.get("credit_card_cvv"),
                card_expiration_date=self.checkout_data.get(
                    "credit_card_validate"
                ),
                card_holder_name=self.checkout_data.get("credit_card_name"),
                installments=self._installments,
                customer=self._customer,
                billing=self._billing,
                shipping=self._shipping,
                items=self._items,
            )
            logger.error("CREDIT CARD RESPONSE")
            logger.debug(f"{_payment}")
            return credit_card_payment(payment=_payment)
        except Exception as e:
            raise e

    def payment_slip(self, db_payment):
        _slip_expire = datetime.now() + timedelta(days=3)
        _payment = SlipPayment(
            amount=db_payment.amount,
            api_key=settings.GATEWAY_API,
            payment_method="boleto",
            customer=self._customer,
            type="individual",
            country="br",
            boleto_expiration_date=_slip_expire.strftime("%Y/%m/%d"),
            email=self._customer.get("email"),
            name=self._customer.get("name"),
            documents=[{"type": "cpf", "number": self.user.document}],
        )

        return slip_payment(payment=_payment)


class ProcessOrder:
    def __init__(
        self,
        checkout_data: CheckoutSchema,
        user,
        affiliate,
        payment_address,
        shipping_address,
    ):
        self.checkout_data = checkout_data
        self.shopping_cart = self.checkout_data.get("shopping_cart")
        self.user = user
        self.affiliate = affiliate
        self.payment_address = payment_address
        self.shipping_address = shipping_address

    def process_order(self):
        try:
            order_db = OrderDB(user_id=self.user.id)
            db_order = order_db.create_order()
            for cart in self.shopping_cart[0].get("itens"):
                order_db.create_order_items(db_order.id, cart)
            return db_order
        except Exception as e:
            logger.erro("Erro ao criar pedido {e}")
            raise e

    def customer(self):
        _customer = {
            "external_id": str(self.user.id),
            "name": self.user.name,
            "type": "individual",
            "country": "br",
            "email": self.user.email,
            "documents": [{"type": "cpf", "number": self.user.document}],
            "phone_numbers": ["+55" + self.user.phone],
            "birthday": self.user.birth_date
            if self.user.birth_date
            else "1965-01-01",
        }
        return _customer

    def billing(self):
        _billing = {
            "name": self.user.name,
            "address": self.payment_address.to_json(),
        }
        return _billing

    def shipping(self):
        _total_amount = Decimal(self.shopping_cart[0].get("total_amount"))
        _shipping = {
            "name": self.user.name,
            "fee": int(_total_amount) * 100,
            "delivery_date": datetime.now().strftime("%Y-%m-%d"),
            "expedited": "true",
            "address": self.shipping_address.to_json(),
        }
        logger.debug(_shipping)
        logger.error(f"{_shipping}")
        return _shipping


class ProcessTransaction:
    def __init__(
        self, checkout_data: CheckoutSchema, user, order, payment_id, affiliate
    ):
        self.checkout_data = checkout_data
        self.user = user
        self.order = order
        self.payment_id = payment_id
        self.affiliate = affiliate

    def transaction(self):
        _shopping_cart = self.checkout_data.get("shopping_cart")
        for cart in _shopping_cart[0].get("itens"):
            db_transaction = CreateTransaction(
                user_id=self.user.id,
                cart=cart,
                order=self.order,
                payment_id=self.payment_id,
                affiliate=self.affiliate,
            ).create_transaction()
        return db_transaction


class Checkout:
    def __init__(
        self, db: Session, checkout_data: CheckoutSchema, affiliate, cupom
    ):
        self.db = db
        self.checkout_data = checkout_data
        self.affiliate = affiliate
        self.cupom = cupom

    def process_checkout(self):
        try:
            _user = User(db=self.db, checkout_data=self.checkout_data).user()
            _payment_address = register_payment_address(
                db=self.db, checkout_data=self.checkout_data, user=_user
            )
            _shipping_address = register_shipping_address(
                db=self.db, checkout_data=self.checkout_data, user=_user
            )
            order = ProcessOrder(
                checkout_data=self.checkout_data,
                user=_user,
                affiliate=self.affiliate,
                payment_address=_payment_address,
                shipping_address=_shipping_address,
            )
            _order = order.process_order()
            payment = ProcessPayment(
                checkout_data=self.checkout_data,
                user=_user,
                affiliate=self.affiliate,
                _billing=order.billing(),
                _shipping=order.shipping(),
                _customer=order.customer(),
            )
            _payment = payment.process_payment()
            ProcessTransaction(
                checkout_data=self.checkout_data,
                user=_user,
                order=_order,
                payment_id=payment.db_payment().id,
                affiliate=self.affiliate,
            ).transaction()

            if (
                _order.order_status == "pending"
                or _order.order_status != "pending"
            ):
                UpdateStatus(
                    payment_data=_payment, order=_order
                ).update_payment_status()
            if "credit-card" in _payment.values():
                _payment_response = PaymentResponse(
                    token=_payment.get("token"),
                    order_id=_order.id,
                    name=_user.name,
                    payment_status="PAGAMENTO REALIZADO",
                    errors=_payment.get("errors"),
                )
            else:
                _payment_response = PaymentResponse(
                    token=_payment.get("token"),
                    order_id=_order.id,
                    name=_user.name,
                    boleto_url=_payment.get("boleto_url"),
                    boleto_barcode=_payment.get("boleto_barcode"),
                    errors=_payment.get("errors"),
                )
            logger.debug(_payment_response)
            self.db.commit()
            return _payment_response

        except Exception as e:
            rollback()
            logger.error(f"----- ERROR PAYMENT {e} ")
            raise e
