# ruff: noqa: I001
import pytest
from unittest.mock import MagicMock
from app.entities.user import UserInDB, Token

URL = '/user'


@pytest.mark.asyncio
async def test_get_token(async_client, mocker):
    # Setup
    mock_user = UserInDB(
        user_id=1,
        email='teste@test.com',
        name='Teste',
        document='12345678901',
        phone='11123456789',
        role_id=1,
        document_type='cpf',
        password='hashed_password',
    )

    mocker.patch('app.user.services.authenticate_user', return_value=mock_user)
    mocker.patch(
        'app.user.services.create_access_token', return_value='mock_access_token',
    )
    mocker.patch('app.user.services.get_role_user', return_value='admin')

    # Act
    response = await async_client.post(
        f'{URL}/token',
        data={'username': mock_user.document, 'password': 'testtest'},
    )

    # Assert
    assert response.status_code == 200
    token = response.json()
    assert 'access_token' in token
    assert 'token_type' in token
    assert token['token_type'] == 'bearer'  # noqa: S105
