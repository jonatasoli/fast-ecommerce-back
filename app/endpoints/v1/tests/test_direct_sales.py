import pytest
from loguru import logger
from fastapi.testclient import TestClient

from app.main import app
from app.endpoints.deps import get_db



transacton_with_shipping = {
        'document': '12345678799',
        'mail': 'mail@jonatasoliveira.me',
        'password': 'asdasd',
        'phone': '12345678901',
        'name': 'Jonatas L Oliveira',
        'address': 'Rua XZ',
        'address_number': '160',
        'address_complement': 'Apto 444',
        'neighborhood': 'Narnia',
        'city': 'São Paulo',
        'state': 'São Paulo',
        'country': 'br',
        'zip_code': '18120000',
        'shipping_is_payment': True,
        'ship_name': '',
        'ship_address': '',
        'ship_address_number': '',
        'ship_address_complement': '',
        'ship_neighborhood': '',
        'ship_city': '',
        'ship_state': 'São Paulo',
        'ship_country': 'br',
        'ship_zip_code': '',
        'payment_method': 'credit-card',
        'shopping_cart': [
            {
                'total_amount': '2000.00',
                'installments': 5,
                'itens': [{'amount': 100000, 'qty': 1, 'product_id': 1, 'product_name': 'course01', 'tangible': True}]
                }],
        'credit_card_name': 'Jonatas L Oliveira',
        'credit_card_number': '5401641103018656',
        'credit_card_cvv': '123', 
        'credit_card_validate': '1220',
        'installments': 5
        }


def test_payment(t_client):
    data = { "transaction": transacton_with_shipping,
             "affiliate": "xyz",
             "cupom": ""
            }
    r = t_client.post("/direct-sales/checkout", json=data)
    response = r.json()
    assert r.status_code == 200
    assert response == {'message': 'asdasd'}
