import pytest
# from app.conftest import override_get_db
from dynaconf import settings
from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.domains.domain_user import get_current_user
from app.endpoints.deps import get_db
from app.main import app
from models.role import Role


def test_roles(t_client, db):
    role_1 = Role(status='active', role='ADMIN')
    role_2 = Role(status='active', role='USER')
    db.add(role_1)
    db.commit()
    db.add(role_2)
    db.commit()
    assert role_1.id == 1
    assert role_2.id == 2


def test_signup(t_client) -> None:

    signup_data = {
        'name': 'Jonatas Luiz de Oliveira',
        'mail': 'contato@jonatasoliveira.com',
        'password': 'asdasd',
        'document': '12345678910',
        'phone': '11912345678',
    }
    r = t_client.post('/user/signup', json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == {'name': 'usuario', 'message': 'adicionado com sucesso'}


def test_invalid_signup(t_client) -> None:
    signup_data = {
        'name': 'Jonatas Luiz de Oliveira',
        'mail': 'contato@jonatasoliveira.me',
        'password': 'asdasd',
    }
    r = t_client.post('/user/signup', json=signup_data)

    response = r.json()
    assert r.status_code == 422


def test_signup_new(t_client) -> None:

    signup_data = {
        'name': 'Jonh Doe',
        'mail': 'contato@jonh.com',
        'password': 'secret',
        'document': '12345678911',
        'phone': '11912345678',
    }
    r = t_client.post('/user/signup', json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == {'name': 'usuario', 'message': 'adicionado com sucesso'}


@pytest.mark.skip()
def test_request_token(t_client):
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    r = t_client.post('/user/token', data)
    response = r.json()

    assert response.get('token_type') == 'bearer'
    assert r.status_code == 200
    assert response.get('role') == 'USER'


@pytest.mark.skip()
def test_get_current_user(t_client):
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    r = t_client.post('/user/token', data)
    response = r.json()

    user = get_current_user(response.get('access_token'))

    assert user.id == 2


@pytest.mark.skip()
def test_auth_dash(t_client):
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    r = t_client.post('/user/token', data)
    response = r.json()
    _headers = {'Authorization': f"Bearer {response.get('access_token')}"}

    output = t_client.get('/user/dashboard', headers=_headers)
    _json = output.json()
    assert output != None
    assert output.status_code == 200
    assert _json['role'] == 'USER'
