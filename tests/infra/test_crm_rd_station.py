"""Tests for crm/rd_station module."""
import pytest
from faker import Faker

from app.infra.crm.rd_station import (
    DEFAULT_SUCESS_CODE,
    NotSendToCRMError,
    send_abandonated_cart_to_crm,
)
from tests.factories import UserDataFactory

fake = Faker()


@pytest.mark.asyncio
async def test_send_abandonated_cart_to_crm_success(mocker):
    """Test send_abandonated_cart_to_crm sends user data successfully."""
    # Setup
    user_data = UserDataFactory()
    mock_settings = mocker.Mock()
    mock_settings.value = {
        'url': fake.url(),
        'access_key': fake.uuid4(),
        'deal_stage_id': str(fake.random_int()),
        'deal_stage_name': fake.sentence(),
    }
    mock_get_settings = mocker.AsyncMock(return_value=mock_settings)
    mock_session = mocker.AsyncMock()
    # db.begin() returns an async context manager
    mock_begin_context = mocker.AsyncMock()
    mock_begin_context.__aenter__ = mocker.AsyncMock(return_value=mock_session)
    mock_begin_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_db = mocker.Mock()
    mock_db.begin = mocker.Mock(return_value=mock_begin_context)

    mock_response = mocker.Mock()
    mock_response.status_code = DEFAULT_SUCESS_CODE
    mock_response.content = b'Success'

    mocker.patch('app.infra.crm.rd_station.requests.post', return_value=mock_response)

    # Act
    await send_abandonated_cart_to_crm(
        user_data,
        get_settings=mock_get_settings,
        db=mock_db,
    )

    # Assert
    mock_get_settings.assert_called_once()
    mock_db.begin.assert_called_once()


@pytest.mark.asyncio
async def test_send_abandonated_cart_to_crm_failure(mocker):
    """Test send_abandonated_cart_to_crm raises error on failure."""
    # Setup
    user_data = UserDataFactory()
    mock_settings = mocker.Mock()
    mock_settings.value = {
        'url': fake.url(),
        'access_key': fake.uuid4(),
        'deal_stage_id': str(fake.random_int()),
        'deal_stage_name': fake.sentence(),
    }
    mock_get_settings = mocker.AsyncMock(return_value=mock_settings)
    mock_session = mocker.AsyncMock()
    mock_begin_context = mocker.AsyncMock()
    mock_begin_context.__aenter__ = mocker.AsyncMock(return_value=mock_session)
    mock_begin_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_db = mocker.Mock()
    mock_db.begin = mocker.Mock(return_value=mock_begin_context)

    mock_response = mocker.Mock()
    mock_response.status_code = 400

    mocker.patch('app.infra.crm.rd_station.requests.post', return_value=mock_response)

    # Act & Assert
    with pytest.raises(NotSendToCRMError):
        await send_abandonated_cart_to_crm(
            user_data,
            get_settings=mock_get_settings,
            db=mock_db,
        )


@pytest.mark.asyncio
async def test_send_abandonated_cart_to_crm_payload_format(mocker):
    """Test send_abandonated_cart_to_crm formats payload correctly."""
    # Setup
    user_data = UserDataFactory()
    deal_stage_id = str(fake.random_int())
    deal_stage_name = fake.sentence()
    mock_settings = mocker.Mock()
    mock_settings.value = {
        'url': fake.url(),
        'access_key': fake.uuid4(),
        'deal_stage_id': deal_stage_id,
        'deal_stage_name': deal_stage_name,
    }
    mock_get_settings = mocker.AsyncMock(return_value=mock_settings)
    mock_session = mocker.AsyncMock()
    mock_begin_context = mocker.AsyncMock()
    mock_begin_context.__aenter__ = mocker.AsyncMock(return_value=mock_session)
    mock_begin_context.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_db = mocker.Mock()
    mock_db.begin = mocker.Mock(return_value=mock_begin_context)

    mock_response = mocker.Mock()
    mock_response.status_code = DEFAULT_SUCESS_CODE
    mock_response.content = b'Success'

    mock_post = mocker.patch('app.infra.crm.rd_station.requests.post')
    mock_post.return_value = mock_response

    # Act
    await send_abandonated_cart_to_crm(
        user_data,
        get_settings=mock_get_settings,
        db=mock_db,
    )

    # Assert
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert 'json' in call_args.kwargs
    payload = call_args.kwargs['json']
    assert payload['deal']['deal_stage_id'] == deal_stage_id
    assert payload['deal']['name'] == deal_stage_name
    assert payload['contacts'][0]['name'] == user_data.name
    assert payload['contacts'][0]['emails'][0]['email'] == user_data.email
    assert payload['contacts'][0]['phones'][0]['phone'] == user_data.phone
