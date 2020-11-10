import pytest

from loguru import logger
from fastapi.testclient import TestClient

from app.main import app
from app.endpoints.deps import get_db


from app.schemas.order_schema import ProductSchema
from domains.domain_order import create_order


def test_create_order(t_client):
    order = {
        "id": 2,
        "customer_id": 1,
        "order_date": "2020-11-11 17:01:01",
        "tracking_number": 2341231,
        "payment_id":1
    }
    r = t_client.post("/order/create_order", json=order)
    response = r.json()
    assert r.status_code == 200
    assert response.get("id") == 2
    

def test_put_order(t_client):
    order = {
        "id": 2,
        "customer_id": 1,
        "order_date": "2020-11-11 17:30:01",
        "tracking_number": 3334131,
        "payment_id":1
    }
    r = t_client.put("/order/2", json=order)
    response = r.json()
    assert r.status_code == 200
    assert response.get("tracking_number") == 3334131

def test_get_order_id(t_client):
    r = t_client.get("/order/1")
    response = r.json()
    assert r.status_code == 200
    assert response.get("name") == "Jonatas L Oliveira"

def test_get_order_user_id(t_client):
    r = t_client.get("/order/user/1")
    response = r.json()
    assert r.status_code == 200
    assert response.get("name") == "User Test"