# ruff: noqa: I001
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.entities.report import UserSalesCommissions, InformUserProduct
from tests.fake_functions import fake_email, fake


@pytest.mark.asyncio
async def test_get_user_sales_commissions(async_client, mocker, async_admin_token):
    # Setup
    mock_commissions = UserSalesCommissions(commissions=[])
    mocker.patch(
        'app.report.services.get_user_sales_commissions', return_value=mock_commissions,
    )
    mocker.patch('app.user.services.get_affiliate_by_token', return_value=MagicMock())

    # Act
    response = await async_client.get(
        '/report/user/comissions',
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['commissions'] == []


@pytest.mark.asyncio
async def test_get_sales_commissions(async_client, mocker, async_admin_token):
    # Setup
    mock_response = UserSalesCommissions(commissions=[])
    mocker.patch(
        'app.report.services.get_sales_commissions', return_value=mock_response,
    )
    mocker.patch('app.user.services.verify_admin', return_value=True)

    # Act
    response = await async_client.get(
        '/report/commissions', headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert 'commissions' in response.json()


@pytest.mark.asyncio
async def test_inform_product_user(async_client, mocker, async_admin_token):
    # Setup
    mocker.patch('app.report.services.notify_product_to_admin', return_value=None)
    mocker.patch(
        'app.infra.endpoints.report.domain_user.get_admin',
        return_value=MagicMock(),
        create=True,
    )

    payload = {
        'product_id': fake.pyint(min_value=1, max_value=1000),
        'email': fake_email(),
        'phone': fake.phone_number(),
    }

    # Act
    response = await async_client.post(
        '/report/inform',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 204
