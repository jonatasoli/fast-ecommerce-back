from fastapi import status
from httpx import AsyncClient
import pytest
from main import app

URL = '/user'

@pytest.mark.skip
async def test_get_token(admin_user):
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.post(
            f'{URL}/token',
            data={'username': admin_user.document, 'password': admin_user.clean_password},
        )
    token = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in token
    assert 'token_type' in token
