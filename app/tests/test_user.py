import pytest
# from sqlalchemy.orm import Session
from loguru import logger
from fastapi.testclient import TestClient

# from app.conftest import override_get_db
from dynaconf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.endpoints.deps import get_db


def test_signup(t_client) -> None:

    signup_data = {
            "name": "Jonatas Luiz de Oliveira",
            "mail": "contato@jonatasoliveira.com",
            "password": "asdasd",
            "document": "12345678910",
            "phone": "11912345678"
            }
    r = t_client.post("/signup", json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == { 
            'name': 'usuario',
            'message': 'adicionado com sucesso'
            }

    
def test_login(t_client) -> None:
    login_data = {
        "document": "12345678910",
        "password": "asdasd"
    }
    r = t_client.post("/login", json=login_data)
    response = r.json()
    assert r.status_code == 200
    assert response == {'message': 'asdasd'}


def test_invalid_signup(t_client) -> None:
    signup_data = {
            "name": "Jonatas Luiz de Oliveira",
            "mail": "contato@jonatasoliveira.me",
            "password": "asdasd",
            }
    r = t_client.post("/signup", json=signup_data)

    response = r.json()
    assert r.status_code == 422

# # if __name__ == "__main__":
# #     signup()
