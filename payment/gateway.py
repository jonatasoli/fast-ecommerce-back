import json

import httpx
from dynaconf import settings
from loguru import logger

from payment.schema import CreditCardPayment, ResponseGateway, SlipPayment


def credit_card_payment(payment: CreditCardPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        logger.debug(f'----- DICT {payment.dict()} ------------')
        logger.debug(f'{settings.PAYMENT_GATEWAY_URL}')
        r = httpx.post(
            f'{settings.PAYMENT_GATEWAY_URL}',
            json=payment.dict(),
            headers=headers,
        )
        logger.error(f'----- request {r.content} --------')
        r = r.json()
        logger.error(f"response error {r.get('errors')}")
        response = ResponseGateway(
            user='usuario',
            token=r.get('acquirer_id'),
            status=r.get('status'),
            authorization_code=r.get('authorization_code'),
            gateway_id=r.get('id'),
            payment_method='credit-card',
            errors=r.get('errors'),
        ).dict()
        return response
    except Exception as e:
        logger.error(f'Erro ao retornar gateway {e}')
        raise e


def slip_payment(payment: SlipPayment):
    try:
        headers = {'Content-Type': 'application/json'}
        logger.debug(f'------------ {payment.json()} ----- PAYMENTJSON')
        logger.debug(f'{settings.PAYMENT_GATEWAY_URL}')
        r = httpx.post(
            f'{settings.PAYMENT_GATEWAY_URL}',
            json=payment.dict(),
            headers=headers,
        )
        r = r.json()
        logger.info(f'RESPONSE ------------{r}')
        response = ResponseGateway(
            user='usuario',
            token=r.get('acquirer_id'),
            status=r.get('status'),
            authorization_code=r.get('authorization_code'),
            gateway_id=r.get('id'),
            payment_method='slip-payment',
            boleto_url=r.get('boleto_url'),
            boleto_barcode=r.get('boletor_barcode'),
            errors=r.get('errors'),
        ).dict()
        return response
    except Exception as e:
        logger.error('Erro ao retornar gateway {e}')
        raise e
