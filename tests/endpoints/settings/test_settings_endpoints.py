import pytest
from unittest.mock import AsyncMock
from app.entities.settings import MainSettings
from tests.fake_functions import fake


@pytest.mark.asyncio
async def test_get_settings(async_client, mocker, async_admin_token):
    # Setup
    site_name = fake.company()
    mock_settings = {'site_name': site_name}
    mocker.patch('app.settings.repository.get_settings', return_value=mock_settings)

    # Act
    response = await async_client.get(
        '/settings/?field=main&locale=en',
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == mock_settings


@pytest.mark.asyncio
async def test_update_settings(async_client, mocker, async_admin_token):
    # Setup
    locale = 'en'
    mock_setting_response = MainSettings(
        locale=locale,
        payment=None,
        logistics=None,
        notification=None,
        cdn=None,
        company=None,
        crm=None,
        mail=None,
    )
    mocker.patch(
        'app.settings.repository.update_or_create_setting',
        return_value=mock_setting_response,
    )
    mocker.patch('app.user.services.verify_admin', return_value=True)

    payload = {
        'locale': locale,
        'payment': None,
        'logistics': None,
        'notification': None,
        'cdn': None,
        'company': None,
        'crm': None,
        'mail': None,
    }

    # Act
    response = await async_client.patch(
        f'/settings/?locale={locale}',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['locale'] == locale
