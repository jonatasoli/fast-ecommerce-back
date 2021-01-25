import pytest
from loguru import logger
from fastapi.testclient import TestClient

from main import app
from endpoints.deps import get_db


from schemas.order_schema import ProductSchema
from domains.domain_order import create_product
from domains.domain_order import create_order

transacton_with_shipping = {
        'document': '86187785088',
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
        'credit_card_number': '5286455462496746',
        'credit_card_cvv': '798', 
        'credit_card_validate': '0822',
        'installments': 5
        }

transacton_with_shipping_and_document_error = {
        'document': '10987654321',
        'mail': 'mail2@jonatasoliveira.me',
        'password': 'asdasd',
        'phone': '12345678910',
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


@pytest.mark.skip
def test_create_product_(db_models): #TODO Fix product ENDPOINT
    db_product = ProductSchema(
            description = "Test Product",
            direct_sales = None,
            installments_config=1,
            name="Teste",
            price=10000,
            upsell=None,
            uri="/test",
            installments_list={
                {"name": "1", "value": "R$100,00"},
                {"name": "2", "value": "R$50,00"},
                {"name": "3", "value": "R$33,00"},
                {"name": "4", "value": "R$25,00"},
                {"name": "5", "value": "R$20,00"}
                }
            )
    db.add(db_product)
    db.commit()
    assert db_product.id == 1

@pytest.mark.first
def test_create_config(t_client):
    _config = {
            "fee": "0.0599",
            "min_installment": 3,
            "max_installment": 12
            }

    r = t_client.post("/create-config", json=_config)
    response = r.json()
    assert r.status_code == 201
    assert response.get('fee') == "0.0599"

@pytest.mark.second
def test_create_product(t_client):
    product = {
            "description":"Test Product",
            "direct_sales":None,
            "installments_config":1,
            "name":"Test",
            "price":10000,
            "upsell":None,
            "uri":"/test",
            "image_path":"https://i.pinimg.com/originals/e4/34/2a/e4342a4e0e968344b75cf50cf1936c09.jpg",
            "quantity": 100,
            "discount": 100,
            "category_id": 1,
            "installments_list":[
            {"name": "1", "value": "R$100,00"},
            {"name": "2", "value": "R$50,00"},
            {"name": "3", "value": "R$33,00"},
            {"name": "4", "value": "R$25,00"},
            {"name": "5", "value": "R$20,00"}
        ]
    }


    r = t_client.post("/create-product", json=product)
    response = r.json()
    assert r.status_code == 201
    assert response.get('name') == "Test"

@pytest.mark.third 
def test_payment(t_client):
    data = { "transaction": transacton_with_shipping,
             "affiliate": "xyz",
             "cupom": "disconunt"
            }
    r = t_client.post("/checkout", json=data)
    response = r.json()
    assert r.status_code == 201
    assert response.get('order_id') == 1
    assert response.get('payment_status') == "PAGAMENTO REALIZADO"

@pytest.mark.fourth
def test_payment_with_document_error(t_client):
    data = { "transaction": transacton_with_shipping_and_document_error,
             "affiliate": "xyz",
             "cupom": ""
            }
    r = t_client.post("/checkout", json=data)
    response = r.json()
    assert r.status_code == 201
    assert response.get('order_id') == 2
    assert response.get('errors')[0].get('message') == "Invalid CPF"
