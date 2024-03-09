from fastapi import status
from app.user.services import gen_hash
from app.infra.models import RoleDB
from tests.factories_db import UserDBFactory, RoleDBFactory


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
    assert response == {
        'name': 'Jonatas Luiz de Oliveira',
        'message': 'Add with sucesso!',
    }


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
    assert response == {'name': 'Jonh Doe', 'message': 'Add with sucesso!'}


def test_request_token(t_client, db):
    _password = gen_hash('secret')
    _name = None
    with db:
        role = RoleDBFactory()
        db.add(role)
        db.commit()
        user_db = UserDBFactory(
            username='12345678911',
            document='12345678911',
            password=_password,
            role_id=role.role_id,
        )
        db.add(user_db)
        db.commit()
        _name = role.role
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    output = t_client.post(
        '/user/token',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data=data,
    )
    response = output.json()

    assert response.get('token_type') == 'bearer'
    assert output.status_code == 200
    assert response.get('role') == f'{_name}'


def test_get_current_user(t_client, db):
    _password = gen_hash('secret')
    _document = '12345678911'
    _name = None
    with db:
        role = RoleDBFactory()
        db.add(role)
        db.commit()
        user_db = UserDBFactory(
            username='12345678911',
            document='12345678911',
            password=_password,
            role_id=role.role_id,
        )
        db.add(user_db)
        db.commit()
        _name = role.role
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    output = t_client.post(
        '/user/token',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data=data,
    )
    response = output.json()

    user_response = t_client.get(
        f'/user/{_document}',
        headers={
            'Authorization': f"Bearer {response.get('access_token')}",
            'accept': 'application/json',
        },
    )

    assert user_response.status_code == status.HTTP_200_OK
