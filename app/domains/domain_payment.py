import requests

from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

from schemas.payment_schema import CreditCardPayment, SlipPayment
from schemas.order_schema import ProductSchema, InvoiceSchema, \
    InvoiceItemsSchema, CheckoutSchema
from schemas.user_schema import SignUp

from models.order import Product, Invoice, InvoiceItems
from models.transaction import Transaction, Payment
from domains.domain_user import create_user, check_existent_user, \
    register_payment_address, register_shipping_address

from constants import DocumentType, Roles

from dynaconf import settings



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
               "authorization_code": r.get("authorization_code"),
               "errors": r.get("errors")}
    except Exception as e:
        raise e


def slip_payment(db: Session, payment: SlipPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        r = requests.post(settings.PAYMENT_GATEWAY_URL, data=payment.json(), headers=headers)
        r = r.json()
        logger.info(f"RESPONSE ------------{r}")
    except Exception as e:
        raise e
    return {"user": "usuario", "status": r.get('status')}


def process_checkout(db: Session, checkout_data: CheckoutSchema, affiliate=None, cupom=None):
    try:
        """
        1 - checar usuário/cadastra usuário
        2 - cadastra end de cobrança
        3 - cadastra end de entrega
        4 - Criar o invoice
        5 - Criar os items do invoice
        6 - Cadastra a transação
        7 - Cadastra o pagamento
        8 - Retorna -> id do gateway - id da order - nome do user
        9 - enviar o e-mail do postback
        """
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
        _payment = process_payment(
                db=db,
                checkout_data=checkout_data,
                user=_user,
                order=_order,
                shipping_address=_shipping_address,
                payment_address=_payment_address)
        if "paid" in _payment.values():
            update_payment_status(db=db, payment_data=_payment, order=_order)
        return {
                'token': _payment.get("token"),
                "order_id": _order.id,
                "name": _user.name,
                "payment_status": 'PAGAMENTO REALIZADO' if _payment.get('status') == 'paid' else ''
                }

    except Exception as e:
        raise e


def check_user(db: Session, checkout_data: CheckoutSchema):
    try:
        # import ipdb; ipdb.set_trace()
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
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        raise e


def process_order(db: Session, shopping_cart, user):
    try:
        db_invoice = Invoice(
                customer_id=user.id,
                invoice_date=datetime.now()
                )
        db.add(db_invoice)
        db.commit()
        for cart in shopping_cart:
            db_item = InvoiceItems(
                    invoice_id = db_invoice.id,
                    product_id = cart.get("product_id"),
                    quantity = cart.get("qty")
                    )
            db.add(db_item)
            db.commit()
            db.refresh(db_invoice)
        db.refresh(db_item)
        return db_invoice

    except Exception as e:
        db.rollback()
        raise e


def process_payment(
        db: Session,
        checkout_data: CheckoutSchema,
        user,
        order,
        shipping_address,
        payment_address):
    try:
        user_id = user.id
        _shopping_cart = checkout_data.get('shopping_cart')
        _total_amount = float(_shopping_cart[0].get("total_amount"))
        _payment_method = checkout_data.get('payment_method')
        _installments = checkout_data.get('installments')
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
                "phone_numbers": [user.phone],
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
            "fee": 1000,
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
                installments=_installments
                )
        db.add(db_payment)
        db.commit()

        _items = [] 
        for cart in _shopping_cart[0].get("itens"):
            logger.debug(cart)
            db_transaction = Transaction(
                    user_id=user_id,
                    amount=cart.get("amount"),
                    invoice=order.id,
                    qty=cart.get("qty"),
                    payment_id=db_payment.id,
                    status="pending",
                    product_id=cart.get("product_id"),
                    affiliate=cart.get("affiliate"),
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
        db.refresh(db_payment)
        db.refresh(db_transaction)

        if checkout_data.get('payment_method') == "credit-card":
            logger.info("------------CREDIT CARD--------------")
            _payment = CreditCardPayment(
                    api_key= settings.GATEWAY_API,
                    amount= db_payment.amount,
                    card_number= checkout_data.get('credit_card_number'),
                    card_cvv= checkout_data.get('credit_card_cvv'),
                    card_expiration_date= checkout_data.get('credit_card_validate'),
                    card_holder_name= checkout_data.get('credit_card_name'),
                    customer= _customer,
                    billing= _billing,
                    shipping= _shipping,
                    items= _items
                    )
            logger.error("CREDIT CARD RESPONSE")
            logger.debug(f"{_payment}")
            return credit_card_payment(db=db, payment=_payment)
        else:
            _payment = {
                    "amount": db_payment.amount,
                    "api_key": settings.GATEWAY_API
                    }
            slip_payment(db=db, payment=_payment )


    except Exception as e:
        db.rollback()
        raise e


def send_payment_mail(db: Session, user, payment):
    try:
        pass
    except Exception as e:
        raise e


def postback_payment(db: Session, payment_data, order):
    try:
        return update_payment_status(db=db, payment_data=payment_data)
    except Exception as e:
        raise e


def update_payment_status(db:Session, payment_data, order):
    try:
        db_transaction = db.query(Transaction).filter_by(invoice=order.id).first()
        db_transaction.status = 'paid'

        db_payment = db.query(Payment).filter_by(id=db_transaction.payment_id).first()
        db_payment.processed=True
        db_payment.processed_at=datetime.now()
        db_payment.token=payment_data.get("token")
        db_payment.authorization=payment_data.get("authorization_code")
        db_payment.status='paid'
        db.add(db_transaction)
        db.add(db_payment)
        db.commit()
        # send_payment_mail(db=db, user=_user, payment=_payment)

    except Exception as e:
        raise e
