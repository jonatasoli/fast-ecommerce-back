from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
from dynaconf import settings

from .repositories import Product, DecreaseProduct, CreateTransaction\
 ,GetCreditCardConfig, CreateTransaction, CreatePayment

from domains.domain_user import register_shipping_address, register_payment_address\
, check_existent_user, create_user
from .schema import CheckoutSchema, CreditCardPayment, SlipPayment
from schemas.user_schema import SignUp
from models.transaction import CreditCardFeeConfig
from models.order import Order, OrderItems
from .gateway import CreditCardGateway, SlipPaymentGateway
from schemas.order_schema import ProductSchema
from loguru import logger


class CreditCardConfig:
    def __init__(self, db: Session, config_data):
        self.db = db
        self.config_data = config_data

    def create_installment_config(self):
        db_config = CreditCardFeeConfig(
            active_date = datetime.now(),
            fee=Decimal(self.config_data.fee),
            min_installment_with_fee=self.config_data.min_installment,
            mx_installments=self.config_data.max_installment
            )
        self.db.add(db_config)
        self.db.commit()
        return db_config


class User:
    def __init__(self, db: Session, checkout_data: CheckoutSchema):
        self.db= db
        self.checkout_data = checkout_data
        self._user_email = checkout_data.get('mail')
        self._password = checkout_data.get('password')
        self._name = checkout_data.get('name')
        self._document = checkout_data.get('document')
        self._phone = checkout_data.get('phone')


    def check_user(self):
        try:
            logger.info(f"DOCUMENT -----------------{self._document}")
            
            _user = check_existent_user(db=self.db, email=self._user_email, document=self._document, password=self._password)
            logger.info("----------------USER----------------")
            logger.info(_user)
            if not _user:
                return self.user_create()
            return _user
        except Exception as e:
            raise e
    

    def user_create(self):
        try:
            _sign_up = SignUp(
                    name= self._name,
                    mail= self._user_email,
                    password= self._password,
                    document= self._document,
                    phone= self._phone
                    )
            _user = create_user(
                    db=self.db,
                    obj_in=_sign_up
                    )
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
    def create_product(db: Session, product: ProductSchema):
        try:
            if not product.upsell:
                    _upsell = None
            elif None in product.upsell:
                _upsell = None
            else:
                _upsell = product.upsell
            db_product = Product(db, product, _upsell).post_product()
            return db_product
        except Exception as e:
            logger.debug(f"PRODUCT ERROR ---- {e}")
            raise e
    

    def decrease():
        _product_decrease = DecreaseProduct.decrease_product()
        _qty_decrease = int(item.get("quantity"))
        if _product_decrease.quantity < 0:
            raise Exception('Produto esgotado')
        else:
            db.add(_product_decrease)
    

class ShoppingCart:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user, affiliate, order):
        self.db = db
        self.checkout_data = checkout_data
        self.user = user
        self._affiliate = affiliate
        self.order = order
        self._shopping_cart = self.checkout_data.get("shopping_cart")
    

    def add_items(self):
        _items = []
        for cart in self._shopping_cart[0].get("itens"):
            logger.debug(cart)
            # db_transaction = CreateTransaction(
            #     user_id=self.user.id, 
            #     cart=cart, 
            #     order=self.order, 
            #     affiliate=self._affiliate, 
            #     db_payment=self.db_payment
            # ).create_transaction()
            _items.append({
                "id": str(cart.get("product_id")),
                "title": cart.get("product_name"),
                "unit_price": cart.get("amount"),
                "quantity": cart.get("qty"),
                "tangible": str(cart.get("tangible"))
            })
            # self.db.add(db_transaction)
            # self.db.commit()
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
            _total_amount = _total_amount * ((1+ _config_installments.fee) ** _installments)
        return _installments


class ProcessOrder:
    def __init__(self, db: Session, shopping_cart, user, payment_address, shipping_address):
        self.db = db
        self.shopping_cart = shopping_cart
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

            for cart in self.shopping_cart:
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
        _total_amount =self.shopping_cart[0].get("total_amount")

        _shipping = {
        "name": self.user.name,
        "fee": _total_amount,
        "delivery_date": datetime.now().strftime("%Y-%m-%d"),
        "expedited": "true",
        "address": self.shipping_address.to_json()
            }
        logger.error(f"{_shipping}")
        return _shipping 


class Payment:
    def __init__(self, db: Session, checkout_data: CheckoutSchema, user, affiliate, order):
        self.db = db
        self.checkout_data = checkout_data
        self.user = user
        self.affiliate = affiliate
        self.order = order
        self.shopping_cart = ShoppingCart(db=db,checkout_data=checkout_data,user=self.user, affiliate=self.affiliate, order=self.order)
        self._installments = self.shopping_cart.installments()
        self._items = self.shopping_cart.add_items()
        self._customer = self.order.customer()
        self._billing = self.order.billing()
        self._shipping = self.order.shipping()

    def db_payment(self):
        db_payment = CreatePayment(
            user_id=self.user.id,
            _total_amount= Decimal(self._shopping_cart[0].get("total_amount")),
            _installments= self._installments,
            _payment_method= self.checkout_data.get('payment_method'),
            db= self.db ).create_payment()
        return db_payment
    
    def process_payment(self):
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
        response = CreditCardGateway(db=self.db, payment=_payment).credit_card()
        return response
        

    def payment_slip():
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
        
        return SlipPaymentGateway(db=self.db, payment=_payment).slip_payment()


class Checkout:
    def process_checkout(db: Session, checkout_data: CheckoutSchema, affiliate=None):
        try:
            _user = User(db=db, checkout_data=checkout_data).check_user()
            _adress = Adress(db=db, checkout_data=checkout_data, user=_user)
            _payment_address = Adress(db=db, checkout_data=checkout_data, user=_user).payment_address()
            _shipping_address = Adress(db=db, checkout_data=checkout_data, user=_user).shipping_address()
            _order = ProcessOrder(
                db=db, 
                user=_user,
                shopping_cart=checkout_data.get('shopping_cart')[0].get("itens"),
                payment_address=_payment_address,
                shipping_address=_shipping_address)

            _payment = Payment(
                db=db, 
                checkout_data=checkout_data, 
                user= _user,
                affiliate= affiliate,
                order= _order
                ).process_payment()

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
            raise HTTPException(status_code=206, detail=f"Erro ao processar o pagamento verifique os dados ou veja o motivo a seguir -> Motivo {e}")

class Email:
    def email():
        pass

class Discount:
    def discount():
        pass