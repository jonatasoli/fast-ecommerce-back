# ruff: noqa: I001
from fastapi import status
from app.user.services import gen_hash
from app.infra.models import RoleDB
from tests.factories_db import UserDBFactory, RoleDBFactory
from tests.fake_functions import fake_cpf, fake, fake_email


def test_roles(db):
    role_1 = RoleDB(active=True, role='ADMIN')
    role_2 = RoleDB(active=True, role='USER')
    with db().begin() as transaction:
        transaction.session.add(role_1)
        transaction.session.flush()
        transaction.session.add(role_2)
        transaction.session.commit()

    assert role_1.role_id is not None
    assert role_2.role_id == role_1.role_id + 1


def test_signup(client) -> None:
    _name = fake.name()
    signup_data = {
        'name': _name,
        'username': fake.user_name(),
        'mail': fake_email(),
        'password': 'asdasd',
        'document': fake_cpf(),
        'phone': fake.phone_number(),
    }
    r = client.post('/user/signup', json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == {
        'name': _name,
        'message': 'Add with sucesso!',
    }


def test_invalid_signup(client) -> None:
    signup_data = {
        'name': fake.name(),
        'mail': fake_email(),
        'password': 'asdasd',
    }
    r = client.post('/user/signup', json=signup_data)

    r.json()
    assert r.status_code == 422


def test_signup_new(client) -> None:
    _name = fake.name()

    signup_data = {
        'name': _name,
        'mail': fake_email(),
        'username': fake.user_name(),
        'password': 'secret',
        'document': fake_cpf(),
        'phone': fake.phone_number(),
    }
    r = client.post('/user/signup', json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == {'name': _name, 'message': 'Add with sucesso!'}


def test_request_token(client, db):
    _password = gen_hash('secret')
    _name = None
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        user_db = UserDBFactory(
            username='12345678911',
            document='12345678911',
            password=_password,
            role=role,
        )
        transaction.session.add(user_db)
        transaction.session.commit()
        # TODO Ajust factory to get correct role
        _name = role.role
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    output = client.post(
        '/user/token',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data=data,
    )
    response = output.json()

    assert response.get('token_type') == 'bearer'
    assert output.status_code == 200
    assert response.get('role')


def test_get_current_user(client, db):
    _password = gen_hash('secret')
    _document = '12345678911'
    with db().begin() as transaction:
        role = RoleDBFactory()
        transaction.session.add(role)
        transaction.session.flush()
        user_db = UserDBFactory(
            username='12345678911',
            document='12345678911',
            password=_password,
            role_id=role.role_id,
        )
        transaction.session.add(user_db)
        transaction.session.commit()
    data = {
        'username': '12345678911',
        'password': 'secret',
    }
    output = client.post(
        '/user/token',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data=data,
    )
    response = output.json()

    user_response = client.get(
        f'/user/{_document}',
        headers={
            'Authorization': f'Bearer {response.get("access_token")}',
            'accept': 'application/json',
        },
    )

    assert user_response.status_code == status.HTTP_200_OK
