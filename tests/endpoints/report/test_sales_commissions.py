from fastapi import status
from httpx import ASGITransport, AsyncClient
import pytest
from app.infra.database import get_async_session
from main import app

URL = '/report'

@pytest.mark.asyncio
async def test_empty_report_should_empy_list(asyncdb, async_admin_token):
    """Should return empty list."""
    # Arrange
    headers = { 'Authorization': f'Bearer {async_admin_token}' }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            f'{URL}/commissions',
            headers=headers,
        )

    # Assert

    assert response.status_code == status.HTTP_200_OK
