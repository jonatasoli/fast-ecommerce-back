from sqlalchemy.orm import Session
from payment.schema import CreditCardPayment, SlipPayment, ResponseGateway
from loguru import logger
from dynaconf import settings
import json
import requests


def credit_card_payment(payment: CreditCardPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        logger.debug(f"{payment.json()}")
        r = requests.post(settings.PAYMENT_GATEWAY_URL, data=payment.json(), headers=headers)
        r = r.json()
        logger.error(f"response error {r.get('errors')}")
        response = ResponseGateway(
            user= "usuario",
            token= r.get('acquirer_id'),
            status= r.get('status'),
            authorization_code=r.get('authorization_code'),
            gateway_id= r.get('id'),
            payment_method= "credit-card",
            errors= r.get('errors')).dict()
        return response
    except Exception as e:
        logger.error('Erro ao retornar gateway {e}')
        raise e


def slip_payment(payment: SlipPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        r = requests.post(settings.PAYMENT_GATEWAY_URL, data=payment.json(), headers=headers)
        r = r.json()
        logger.info(f"RESPONSE ------------{r}")
        response = ResponseGateway(
            user= "usuario",
            token= r.get('acquirer_id'),
            status= r.get('status'),
            authorization_code=r.get('authorization_code'),
            gateway_id= r.get('id'),
            payment_method= "slip-payment",
            boleto_url=r.get('boleto_url'),
            boleto_barcode=r.get('boletor_barcode'),
            errors=r.get('errors')).dict()
        return response
    except Exception as e:
        logger.error('Erro ao retornar gateway {e}')
        raise e
