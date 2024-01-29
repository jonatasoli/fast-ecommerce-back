import pytest
from domains.domain_user import get_current_user
from app.infra.models import RoleDB


def test_roles(db):
    role_1 = RoleDB(active=True, role='ADMIN')
    role_2 = RoleDB(active=True, role='USER')
    with db:
        db.add(role_1)
        db.commit()
        db.add(role_2)
        db.commit()

        assert role_1.role_id == 1
        assert role_2.role_id == 2


def test_signup(t_client) -> None:

    signup_data = {
        'name': 'Jonatas Luiz de Oliveira',
        'username': 'jonhdoe',
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

    r.json()
    assert r.status_code == 422


def test_signup_new(t_client) -> None:

    signup_data = {
        'name': 'Jonh Doe',
        'mail': 'contato@jonh.com',
        'username': 'johndoe',
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
    assert output is not None
    assert output.status_code == 200
    assert _json['role'] == 'USER'
