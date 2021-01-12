from sqlalchemy.orm import Session
from .schema import CreditCardPayment, SlipPayment
from dynaconf import settings
from loguru import logger
import json
import requests


class CreditCardGateway:
    def __init__(self, db: Session, payment: CreditCardPayment):
        self.db = db
        self.payment = payment


    def credit_card(self):
        try:
            headers = {'Content-Type': 'application/json'}
            r = requests.post(settings.PAYMENT_GATEWAY_URL, data=self.payment.json(), headers=headers)
            logger.error(f"response error {r.get('errors')}")
            logger.info(f"RESPONSE ------------{r}")
            r = r.json()
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


class SlipPaymentGateway:
    def __init__(self, db: Session, payment: SlipPayment):
        self.db= db
        self.payment = payment


    def slip_payment(self):
        try:
            headers = {'Content-Type': 'application/json'}
            r = requests.post(settings.PAYMENT_GATEWAY_URL, data=self.payment.json(), headers=headers)
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