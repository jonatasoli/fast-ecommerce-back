import pytest
from dynaconf import settings


def test_payment_in_gateway_transaction_credit_card(test_client, db) -> None:
    payment_data = {
            "api_key": settings.GATEWAY_API,
            "amount": 21000,
            "card_number": "4111111111111111",
            "card_cvv": "123",
            "card_expiration_date": "0922",
            "card_holder_name": "Morpheus Fishburne",
            "customer": {
                "external_id": "#3311",
                "name": "Morpheus Fishburne",
                "type": "individual",
                "country": "br",
                "email": "mopheus@nabucodonozor.com",
                "documents": [
                    {
                        "type": "cpf",
                        "number": "00000000000"
                        }
                    ],
                "phone_numbers": ["+5511999998888", "+5511888889999"],
                "birthday": "1965-01-01"
                },
            "billing": {
                "name": "Trinity Moss",
                "address": {
                    "country": "br",
                    "state": "sp",
                    "city": "Cotia",
                    "neighborhood": "Rio Cotia",
                    "street": "Rua Matrix",
                    "street_number": "9999",
                    "zipcode": "06714360"
                    }
                },
            "shipping": {
                "name": "Neo Reeves",
                "fee": 1000,
                "delivery_date": "2000-12-21",
                "expedited": "true",
                "address": {
                    "country": "br",
                    "state": "sp",
                    "city": "Cotia",
                    "neighborhood": "Rio Cotia",
                    "street": "Rua Matrix",
                    "street_number": "9999",
                    "zipcode": "06714360"
                    }
                },
            "items": [
                {
                    "id": "r123",
                    "title": "Red pill",
                    "unit_price": 10000,
                    "quantity": 1,
                    "tangible": "true"
                    },
                {
                    "id": "b123",
                    "title": "Blue pill",
                    "unit_price": 10000,
                    "quantity": 1,
                    "tangible": "true"
                    }
                ]           

            }
    r = test_client.post("/gateway-payment-credit-card", json=payment_data)

    response = r.json()
    assert r.status_code == 201
    assert response == { 
            'user': 'usuario',
            'status': 'paid',
            }


def test_payment_in_gateway_transaction_bank_slip(test_client, db) -> None:
    payment_data = {
            "amount": 2100, 
            "api_key": settings.GATEWAY_API,
            "payment_method": "boleto",
            "customer":{
                "type": "individual",
                "country": "br",
                "name": "Daenerys Targaryen",
                "documents": [{
                    "type": "cpf",
                    "number": "00000000000"
                    }]
                }
            }
    r = test_client.post("/gateway-payment-bank-slip", json=payment_data)

    response = r.json()
    assert r.status_code == 201
    assert response == { 
            'user': 'usuario',
            'status': 'waiting_payment',
            }


def test_check_user(test_client, db) -> None:

    signup_data = {
            "name": "Jonatas Oliveira",
            "mail": "teste+contato@jonatasoliveira.me",
            "password": "asdasd",
            "document": "02345678910",
            "phone": "11922345678"
            }
    r = test_client.post("/signup", json=signup_data)
    
    payment_data = {
             }

def test_payment_logged_user(test_client, db) -> None:
    pass


def test_payment_not_logged_user(test_client, db) -> None:
    pass


def test_payment_with_affiliate(test_client, db) -> None:
    pass

