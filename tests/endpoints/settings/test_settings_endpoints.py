import pytest
from unittest.mock import AsyncMock
from app.entities.settings import MainSettings
from tests.fake_functions import fake


@pytest.mark.asyncio
async def test_get_settings(async_client, mocker, async_admin_token):
    # Setup
    from app.infra.models import SettingsDB
    from app.entities.settings import SettingsResponse
    mock_setting_db = SettingsDB(
        settings_id=1,
        locale='en',
        provider='test',
        field='main',
        value={'site_name': 'Test Company'},
        credentials=None,
        description=None,
        is_active=True,
        is_default=False,
    )
    mocker.patch(
        'app.settings.repository.list_settings',
        return_value=([mock_setting_db], 1),
    )

    # Act
    response = await async_client.get(
        '/settings/?field=main&locale=en',
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    assert response.status_code == 200
    data = response.json()
    assert 'settings' in data
    assert 'total' in data
    assert data['total'] == 1
    assert len(data['settings']) == 1
    assert data['settings'][0]['field'] == 'main'


@pytest.mark.asyncio
async def test_update_settings(async_client, mocker, async_admin_token):
    # Setup
    from app.infra.models import SettingsDB
    locale = 'en'
    mock_setting_db = SettingsDB(
        settings_id=1,
        locale=locale,
        provider='test',
        field='main',
        value={},
        credentials=None,
        description=None,
        is_active=True,
        is_default=False,
    )
    mocker.patch(
        'app.settings.repository.update_or_create_setting',
        return_value=mock_setting_db,
    )

    payload = {
        'locale': locale,
        'is_default': False,
        'payment': None,
        'logistics': None,
        'notification': None,
        'cdn': None,
        'company': None,
        'crm': None,
        'mail': None,
        'bucket': None,
    }

    # Act
    response = await async_client.patch(
        f'/settings/legacy?locale={locale}',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    assert response.status_code == 200
    data = response.json()
    assert data['locale'] == locale
