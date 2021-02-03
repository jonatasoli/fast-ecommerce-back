
import requests
import json

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from loguru import logger

from schemas.payment_schema import CreditCardPayment, SlipPayment
from schemas.order_schema import ProductSchema, OrderSchema, \
    OrderItemsSchema, CheckoutSchema
from schemas.user_schema import SignUp

from models.order import Product, Order, OrderItems
from models.transaction import Transaction, Payment, CreditCardFeeConfig
from domains.domain_user import create_user, check_existent_user, \
    register_payment_address, register_shipping_address

from constants import DocumentType, Roles

from dynaconf import settings


def create_installment_config(db: Session, config_data):
    db_config = CreditCardFeeConfig(
            active_date = datetime.now(),
            fee=Decimal(config_data.fee),
            min_installment_with_fee=config_data.min_installment,
            mx_installments=config_data.max_installment
            )
    db.add(db_config)
    db.commit()
    return db_config



def credit_card_payment(db: Session, payment: CreditCardPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        logger.debug(f"{payment.json()}")
        r = requests.post(settings.PAYMENT_GATEWAY_URL, data=payment.json(), headers=headers)
        r = r.json()
        logger.error(f"response error {r.get('errors')}")
        return {
               "user": "usuario",
               "token": r.get("acquirer_id"),
               "status": r.get('status'),
               "authorization_code": r.get('authorization_code'),
               "gateway_id": r.get("id"),
               "payment_method": "credit-card",
               "errors": r.get("errors")}
    except Exception as e:
        raise e


def slip_payment(db: Session, payment: SlipPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        r = requests.post(settings.PAYMENT_GATEWAY_URL, data=payment.json(), headers=headers)
        r = r.json()
        logger.info(f"RESPONSE ------------{r}")
        return {
               "user": "usuario",
               "token": r.get("acquirer_id"),
               "status": r.get('status'),
               "authorization_code": r.get("authorization_code"),
               "payment_method": "slip-payment",
               "boleto_url":  r.get("boleto_url"),
               "boleto_barcode": r.get("boleto_barcode"),
               "gateway_id": r.get("id"),
               "errors": r.get("errors")}
    except Exception as e:
        raise e


def process_checkout(db: Session, checkout_data: CheckoutSchema, affiliate=None, cupom=None):
    try:
        _user = check_user(db=db, checkout_data=checkout_data)
        _payment_address = register_payment_address(
                db=db,
                checkout_data=checkout_data,
                user=_user)
        _shipping_address = register_shipping_address(
                db=db,
                checkout_data=checkout_data,
                user=_user)
        logger.info(f"SHIPPING--------------{_shipping_address}---------------")
        _order = process_order(
                db=db,
                shopping_cart=checkout_data.get('shopping_cart')[0].get("itens"),
                user=_user)
        logger.info(_order)
        _payment = process_payment(
                db=db,
                checkout_data=checkout_data,
                user=_user,
                order=_order,
                shipping_address=_shipping_address,
                payment_address=_payment_address,
                affiliate=affiliate,
                cupom=cupom)

        if _order.order_status == 'pending':
            update_gateway_id(db=db, payment_data=_payment, order=_order)
        if _order.order_status == 'pending' or _order.order_status != 'pending':
            update_payment_status(db=db, payment_data=_payment, order=_order)
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
        db.rollback()
        logger.error(f"----- ERROR PAYMENT {e} ")
        raise HTTPException(status_code=206, detail=f"Erro ao processar o pagamento verifique os dados ou veja o motivo a seguir -> Motivo {e}") 


def check_user(db: Session, checkout_data: CheckoutSchema):
    try:
        _user_email = checkout_data.get('mail')
        _password = checkout_data.get('password')
        _name = checkout_data.get('name')
        _document = checkout_data.get('document')
        _phone = checkout_data.get('phone')
        logger.info(f"DOCUMENT -----------------{_document}")
        

        _user = check_existent_user(db=db, email=_user_email, document=_document, password=_password)
        logger.info("----------------USER----------------")
        logger.info(_user)
        if not _user:
            _sign_up = SignUp(
                    name= _name,
                    mail= _user_email,
                    password= _password,
                    document= _document,
                    phone= _phone
                    )
            _user = create_user(
                    db=db,
                    obj_in=_sign_up
                    )
        return _user
    except Exception as e:
        raise e


def create_product(db: Session, product: ProductSchema):
    try:
        if not product.upsell:
            _upsell = None
        elif None in product.upsell:
            _upsell = None
        else:
            _upsell = product.upsell
        db_product = Product(
                name=product.name,
                price=product.price,
                direct_sales=product.direct_sales,
                upsell=_upsell
                )
        db.add(db_product)
        db.commit()
        return db_product
    except Exception as e:
        logger.debug(f"PRODUCT ERROR ---- {e}")
        raise e


def process_order(db: Session, shopping_cart, user):
    try:
        db_order = Order(
                customer_id=user.id,
                order_date=datetime.now(),
                order_status = 'pending')
        db.add(db_order)
        for cart in shopping_cart:
            db_item = OrderItems(
                    order_id = db_order.id,
                    product_id = cart.get("product_id"),
                    quantity = cart.get("qty")
                    )
            db.add(db_item)
        db.commit()
        return db_order

    except Exception as e:
        db.rollback()
        raise e


def process_payment(
        db: Session,
        checkout_data: CheckoutSchema,
        user,
        order,
        shipping_address,
        payment_address,
        affiliate,
        cupom):
    try:
        user_id = user.id
        _shopping_cart = checkout_data.get('shopping_cart')
        _total_amount = Decimal(_shopping_cart[0].get("total_amount"))
        _payment_method = checkout_data.get('payment_method')
        _installments = checkout_data.get('installments')
        if _installments:
            _installments = int(_installments)
        else:
            _installments = 1
        _affiliate = affiliate
        _cupom = cupom
        # TODO refactor config instalments to many products
        _product_id = checkout_data['shopping_cart'][0]['itens'][0]['product_id']
        _product_config = db.query(Product).filter_by(id=int(_product_id)).first()

        _config_installments = db.query(CreditCardFeeConfig)\
            .filter_by(id=_product_config.installments_config)\
            .first()
        if _installments > 12:
            raise Exception("O número máximo de parcelas é 12") 
        elif _installments >= _config_installments.min_installment_with_fee:
            _total_amount = _total_amount * ((1+_config_installments.fee) ** _installments)

        _customer = {
                "external_id": str(user.id),
                "name": user.name,
                "type": "individual",
                "country": "br",
                "email": user.email,
                "documents": [
                    {
                        "type": "cpf",
                        "number": user.document
                    }],
                "phone_numbers": ["+55" + user.phone],
                "birthday": user.birth_date if user.birth_date else "1965-01-01",
                }
        _billing = {
            "name": user.name,
            "address": payment_address.to_json()
                }
        logger.debug("--------- SHIPPING ----------")
        logger.debug(f"SHIPPING      {shipping_address.to_json()}")
        _shipping = {
            "name": user.name,
            "fee": int(_total_amount)*100,
            "delivery_date": datetime.now().strftime("%Y-%m-%d"),
            "expedited": "true",
            "address": shipping_address.to_json()
                }
        logger.error(f"{_shipping}")
    
        db_payment = Payment(
                user_id=user_id,
                amount=int(_total_amount)*100,
                status="pending",
                payment_method=_payment_method,
                payment_gateway="PagarMe",
                installments=_installments if _installments else 1
                )
        db.add(db_payment)
        db.commit()

        _items = [] 
        for cart in _shopping_cart[0].get("itens"):
            logger.debug(cart)
            db_transaction = Transaction(
                    user_id=user_id,
                    amount=cart.get("amount"),
                    order_id=order.id,
                    qty=cart.get("qty"),
                    payment_id=db_payment.id,
                    status="pending",
                    product_id=cart.get("product_id"),
                    affiliate=_affiliate,
                    )
            _items.append({
                "id": str(cart.get("product_id")),
                "title": cart.get("product_name"),
                "unit_price": cart.get("amount"),
                "quantity": cart.get("qty"),
                "tangible": str(cart.get("tangible"))
                })
            db.add(db_transaction)
        db.commit()

        for item in _items:
            _product_decrease = db.query(Product).filter_by(id=item.get("id")).first()
            _qty_decrease = int(item.get("quantity"))
            _product_decrease.quantity -= _qty_decrease
            if _product_decrease.quantity < 0:
                raise Exception('Produto esgotado')
            else:
                db.add(_product_decrease)

        if checkout_data.get('payment_method') == "credit-card":
            logger.info("------------CREDIT CARD--------------")
            _payment = CreditCardPayment(
                    api_key= settings.GATEWAY_API,
                    amount= db_payment.amount,
                    card_number= checkout_data.get('credit_card_number'),
                    card_cvv= checkout_data.get('credit_card_cvv'),
                    card_expiration_date= checkout_data.get('credit_card_validate'),
                    card_holder_name= checkout_data.get('credit_card_name'),
                    installments= _installments,
                    customer= _customer,
                    billing= _billing,
                    shipping= _shipping,
                    items= _items
                    )
            logger.error("CREDIT CARD RESPONSE")
            logger.debug(f"{_payment}")
            return credit_card_payment(db=db, payment=_payment)
        else:
            _slip_expire = datetime.now() + timedelta(days=3)
            _payment = SlipPayment(
                    amount= db_payment.amount,
                    api_key= settings.GATEWAY_API,
                    payment_method= "boleto",
                    customer= _customer,
                    type= "individual",
                    country= "br",
                    # postback_url= "api.graciellegatto.com.br/payment-postback",
                    boleto_expiration_date= _slip_expire.strftime("%Y/%m/%d"),
                    email= _customer.get("email"),
                    name= _customer.get("name"),
                    documents= [
                        {
                            
                            "type":  "cpf",
                            "number": user.document 
                        }
                        ]
                    )
            return slip_payment(db=db, payment=_payment )


    except Exception as e:
        raise e


def send_payment_mail(db: Session, user, payment):
    try:
        pass
    except Exception as e:
        raise e


def postback_payment(db: Session, payment_data, order):
    try:
        return update_payment_status(db=db, payment_data=payment_data, order=order)
    except Exception as e:
        raise e

def update_gateway_id(db:Session, payment_data, order):
    try:
        db_transaction = db.query(Transaction).filter_by(order_id=order.id).first()
        db_payment = db.query(Payment).filter_by(id=db_transaction.payment_id).first()

        db_payment.gateway_id=payment_data.get("gateway_id")
        order.payment_id = payment_data.get("gateway_id")
        db.add(db_payment)
        db.commit()

    except Exception as e:
        raise e

def update_payment_status(db:Session, payment_data, order):
    try:
        db_transaction = db.query(Transaction).filter_by(order_id=order.id).first()
        db_transaction.status = payment_data.get("status")

        db_payment = db.query(Payment).filter_by(id=db_transaction.payment_id).first()
        db_payment.processed=True
        db_payment.processed_at=datetime.now()
        db_payment.token=payment_data.get("token")
        db_payment.authorization=payment_data.get("authorization_code")
        db_payment.status=payment_data.get("status")
        db.add(db_transaction)
        db.add(db_payment)
        db.commit()
        db.refresh(db_transaction)
        db.refresh(db_payment)
        # send_payment_mail(db=db, user=_user, payment=_payment)

    except Exception as e:
        raise e
