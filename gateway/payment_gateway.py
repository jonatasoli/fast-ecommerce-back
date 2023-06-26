import json

import httpx
from dynaconf import settings


def return_transaction(gateway_id):
    try:
        headers = {
            'Content-Type': 'application/json',
            'date_created': '2017-08-15T16:14:58.903Z',
        }
        data = {'api_key': settings.GATEWAY_API}
        r = httpx.get(
            f'https://api.pagar.me/1/transactions/{gateway_id}',
            headers=headers,
            json=data,
        )
        r = r.json()
        return {'gateway_id': r.get('tid'), 'status': r.get('status')}
    except Exception as e:
        raise e
