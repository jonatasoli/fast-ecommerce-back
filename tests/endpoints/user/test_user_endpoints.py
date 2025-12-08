# ruff: noqa: I001
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.entities.user import (
    UserInDB,
    SignUpResponse,
    Token,
    UserSchema,
    UserCouponResponse,
    UsersDBResponse,
)
from tests.fake_functions import fake_email, fake_cpf, fake
from tests.factories import UserDataFactory


@pytest.mark.asyncio
async def test_signup(async_client, mocker):
    # Setup
    name = fake.name()
    email = fake_email()
    mock_response = SignUpResponse(name=name, message='User created')
    mocker.patch('app.user.services.create_user', return_value=mock_response)

    payload = {
        'mail': email,
        'password': fake.password(),
        'name': name,
        'username': fake.user_name(),
        'document': fake_cpf(),
        'phone': fake.phone_number(),
        'terms': True,
    }

    # Act
    response = await async_client.post('/user/signup', json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json()['name'] == name


@pytest.mark.asyncio
async def test_get_user(async_client, mocker, async_admin_token):
    # Setup
    user_data = UserDataFactory()
    mock_user = UserSchema(
        email=user_data.email,
        name=user_data.name,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        user_id=user_data.user_id,
        password='hashed',
    )
    mocker.patch('app.user.services.get_current_user', return_value=mock_user)

    # Act
    response = await async_client.get(
        f'/user/{user_data.document}',
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['email'] == user_data.email


@pytest.mark.asyncio
async def test_get_users(async_client, mocker, async_admin_token):
    # Setup
    mock_response = UsersDBResponse(
        users=[], page=1, limit=10, total_pages=0, total_records=0,
    )
    mocker.patch('app.user.repository.get_users', return_value=mock_response)
    mocker.patch('app.user.services.verify_admin', return_value=True)

    # Act
    response = await async_client.get(
        '/users/', headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['total_records'] == 0


@pytest.mark.asyncio
async def test_update_user(async_client, mocker, async_admin_token):
    # Setup
    user_data = UserDataFactory()
    updated_name = fake.name()
    mock_user = UserInDB(
        email=user_data.email,
        name=updated_name,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        user_id=user_data.user_id,
        document_type='cpf',
        password='hash',
    )
    mocker.patch('app.user.services.update_user', return_value=mock_user)
    mocker.patch('app.user.services.verify_admin', return_value=True)

    payload = {'name': updated_name}

    # Act
    response = await async_client.patch(
        f'/user/{user_data.user_id}',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['name'] == updated_name
