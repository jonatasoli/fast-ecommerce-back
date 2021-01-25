from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from dynaconf import settings
from domains.domain_user import register_payment_address, register_shipping_address
from payment.repositories import Product, DecreaseProduct, CreateTransaction\
 ,GetCreditCardConfig, CreateTransaction, CreatePayment, QueryPayment,\
     UpdateStatus

from payment.adapter import AdapterUser
from payment.schema import CheckoutSchema, CreditCardPayment, SlipPayment
from schemas.user_schema import SignUp
from models.transaction import CreditCardFeeConfig, Transaction, Payment
from models.order import Order, OrderItems
from payment.gateway import credit_card_payment, slip_payment
from schemas.order_schema import ProductSchema
from loguru import logger


class User:
    def __init__(self, db: Session, checkout_data: CheckoutSchema):
        self.db= db
        self.checkout_data = checkout_data
        self._user_email = checkout_data.get('mail')
        self._password = checkout_data.get('password')
        self._name = checkout_data.get('name')
        self._document = checkout_data.get('document')
        self._phone = checkout_data.get('phone')

    def user(self):
        try:
            _user = AdapterUser(
                db= self.db,
                _user_email = self._user_email,
                _password = self._password,
                _name = self._name,
                _document = self._document,
                _phone = self._phone).check_user()
            return _user
        except Exception as e:
            raise e
        

class Adress:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user):
        self.db = db
        self.checkout_data = checkout_data
        self.user = user


    def payment_address(self):
        _payment_address = register_payment_address(
            db=self.db,
            checkout_data=self.checkout_data,
            user=self.user
        )
        return _payment_address


    def shipping_address(self):
        _shipping_address = register_shipping_address(
            db=self.db,
            checkout_data=self.checkout_data,
            user=self.user
        )
        return _shipping_address


class Product:
    def __init__(self, db:Session, item):
        self.db = db
        self.item = item 


    def decrease(self):
        _product_decrease = DecreaseProduct(db=self.db, item= self.item).decrease_product()
        _qty_decrease = int(self.item.get("quantity"))
        _product_decrease.quantity -= _qty_decrease
        if _product_decrease.quantity < 0:
            raise Exception('Produto esgotado')
        else:
            self.db.add(_product_decrease)
    

class ShoppingCart:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user):
        self.db = db
        self.checkout_data = checkout_data
        self.user = user
        self._shopping_cart = self.checkout_data.get("shopping_cart")
        

    def cart(self):
        for cart in self._shopping_cart[0].get("itens"):
            return cart


    def add_items(self):
        _items = []
        for cart in self._shopping_cart[0].get("itens"):
            logger.debug(cart)
            _items.append({
                "id": str(cart.get("product_id")),
                "title": cart.get("product_name"),
                "unit_price": cart.get("amount"),
                "quantity": cart.get("qty"),
                "tangible": str(cart.get("tangible"))
            })
            for item in _items:
                Product(db=self.db, item=item).decrease()
            return _items


    def installments(self):
        _total_amount = Decimal(self._shopping_cart[0].get("total_amount"))
        _installments = self.checkout_data.get("installments")
        _config_installments = GetCreditCardConfig(self.db, self.checkout_data['shopping_cart'][0]['itens'][0]['product_id'])\
        .get_config()
        if _installments:
            _installments= int(_installments)
        else:
            _installments = 1
        if _installments > 12:
            raise Exception("O número máximo de parcelas é 12")
        elif _installments >= _config_installments.min_installment_with_fee:
            _total_amount = _total_amount * ((1+ Decimal(_config_installments.fee)) ** _installments)
        return _installments


class ProcessOrder:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user, payment_address, shipping_address):
        self.db = db
        self.checkout_data = checkout_data
        self.shopping_cart = self.checkout_data.get('shopping_cart')
        self.user = user
        self.payment_address = payment_address
        self.shipping_address = shipping_address


    def process_order(self):
        try:
            db_order = Order(
                customer_id=self.user.id,
                order_date=datetime.now(),
                order_status = 'pending')
            self.db.add(db_order)

            for cart in self.shopping_cart[0].get('itens'):
                db_item = OrderItems(
                    order_id = db_order.id,
                    product_id = cart.get("product_id"),
                    quantity = cart.get("qty")
                    )
                self.db.add(db_item)
            self.db.commit()
            return db_order

        except Exception as e:
            self.db.rollback()
            raise e
    
    
    def customer(self):
        _customer = {
            "external_id": str(self.user.id),
            "name": self.user.name,
            "type": "individual",
            "country": "br",
            "email": self.user.email,
            "documents": [
                {
                    "type": "cpf",
                    "number": self.user.document
                }],
            "phone_numbers": ["+55" + self.user.phone],
            "birthday": self.user.birth_date if self.user.birth_date else "1965-01-01",
            }
        return _customer
        

    def billing(self):
        _billing = {
            "name": self.user.name,
            "address": self.payment_address.to_json()
            }
        return _billing


    def shipping(self):
        _total_amount = Decimal(self.shopping_cart[0].get('total_amount'))
        _shipping = {
        "name": self.user.name,
        "fee": int(_total_amount)*100,
        "delivery_date": datetime.now().strftime("%Y-%m-%d"),
        "expedited": "true",
        "address": self.shipping_address.to_json()
            }
        logger.debug(_shipping)
        logger.error(f"{_shipping}")
        return _shipping

class ProcessTransaction:
    def __init__(self, db:Session, user, order, payment_id, affiliate, cart, _items):
        self.db=db
        self.user = user
        self.order = order
        self.payment_id = payment_id
        self.affiliate = affiliate
        self.cart = cart
        self._items = _items

    def transaction(self):
        db_transaction = CreateTransaction(
                user_id=self.user.id, 
                cart=self.cart, 
                order=self.order, 
                payment_id=self.payment_id,
                affiliate=self.affiliate
                ).create_transaction()
        return db_transaction
    
    def transaction_for_item(self):
        for item in self._items:
            db_transaction = self.transaction()
            self.db.add(db_transaction)
            self.db.commit()

class ProcessPayment:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user, affiliate, order, _customer, _billing, _shipping, shopping_cart):
        self.db = db
        self.checkout_data = checkout_data
        self.user = user
        self.affiliate = affiliate
        self.order = order
        self.shopping_cart = shopping_cart
        self._installments = self.shopping_cart.installments()
        self._items = self.shopping_cart.add_items()
        self._customer = _customer
        self._billing = _billing
        self._shipping = _shipping
 

    def db_payment(self):
        db_payment = CreatePayment(
            user_id=self.user.id,
            _installments= self._installments,
            _payment_method= self.checkout_data.get('payment_method'),
            db= self.db ).create_payment()
        return db_payment
    

    def process_payment(self):
        self.db_payment()
        if self.checkout_data.get('payment_method') == 'credit-card':
            return self.payment_credit_card()
        else:
            return self.payment_slip()
       
    
    def payment_credit_card(self):
        _payment = CreditCardPayment(
            api_key= settings.GATEWAY_API,
            amount= 100,
            card_number= self.checkout_data.get('credit_card_number'),
            card_cvv= self.checkout_data.get('credit_card_cvv'),
            card_expiration_date= self.checkout_data.get('credit_card_validate'),
            card_holder_name= self.checkout_data.get('credit_card_name'),
            installments= self._installments,
            customer= self._customer,
            billing= self._billing,
            shipping= self._shipping,
            items= self._items
        )
        logger.error("CREDIT CARD RESPONSE")
        logger.debug(f"{_payment}")
        return credit_card_payment(db=self.db, payment=_payment)
    

    def payment_slip(self):
        _slip_expire = datetime.now() + timedelta(days=3)
        _payment = SlipPayment(
                amount= 100,
                api_key= settings.GATEWAY_API,
                payment_method= "boleto",
                customer= self._customer,
                type= "individual",
                country= "br",
                # postback_url= "api.graciellegatto.com.br/payment-postback",
                boleto_expiration_date= _slip_expire.strftime("%Y/%m/%d"),
                email= self._customer.get("email"),
                name= self._customer.get("name"),
                documents= [
                    {
                        "type":  "cpf",
                        "number": self.user.document 
                    }
                    ]
                )
        
        return slip_payment(db=self.db, payment=_payment)


class Checkout:
    def process_checkout(db: Session, checkout_data: CheckoutSchema, affiliate=None, cupom=None):
        try:
            _user = User(db=db, checkout_data=checkout_data).user()
            _adress = Adress(db=db, checkout_data=checkout_data, user=_user)
            _payment_address = register_payment_address(db=db, checkout_data=checkout_data, user=_user)
            _shipping_address = register_shipping_address(db=db, checkout_data=checkout_data, user=_user)
            order = ProcessOrder(
                db=db,
                checkout_data=checkout_data,
                user=_user,
                payment_address=_payment_address,
                shipping_address=_shipping_address)
            _order = order.process_order()
            _shopping_cart = ShoppingCart(db=db, checkout_data=checkout_data, user=_user)
            payment = ProcessPayment(
                db=db, 
                checkout_data=checkout_data, 
                user= _user,
                affiliate= affiliate,
                order= _order,
                _customer= order.customer(),
                _billing=order.billing(),
                _shipping=order.shipping(),
                shopping_cart= _shopping_cart
                )
            _payment = payment.process_payment()

            _transaction = ProcessTransaction(db=db, user=_user, order=_order, affiliate=affiliate, payment_id=payment.db_payment().id, cart=_shopping_cart.cart(), _items=_shopping_cart.add_items())
            _transaction.transaction_for_item()
            if _order.order_status == 'pending':
                UpdateStatus.update_payment_status(db=db, payment_data=_payment, order= _order)
            if "credit-card" in _payment.values():
                _payment_response = {
                    'token': _payment.get("token"),
                    "order_id": _order.id,
                    "name": _user.name,
                    "payment_status": 'PAGAMENTO REALIZADO' if _payment.get('status') == 'paid' else '',
                    "errors": _payment.get("errors")
                    }
            else:
                _payment_response = {
                    'token': _payment.get("token"),
                    "order_id": _order.id,
                    "name": _user.name,
                    "boleto_url":  _payment.get("boleto_url"),
                    "boleto_barcode": _payment.get("boleto_barcode"),
                    "errors": _payment.get("errors")
                        }
            logger.debug(_payment_response)
            db.commit()
            return _payment_response

        except Exception as e:
            # db.rollback()
            logger.error(f"----- ERROR PAYMENT {e} ")
            raise e


class Email:
    def email():
        pass

class Discount:
    def discount():
        pass
