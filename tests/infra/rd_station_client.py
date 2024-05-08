from app.entities.user import UserData
import pytest
from unittest.mock import AsyncMock

from app.infra.crm.rd_station import NotSendToCRMError, send_abandonated_cart_to_crm
from pydantic import BaseModel

class MockRequestResponse(BaseModel):
    value: dict

@pytest.mark.asyncio()
async def test_successful_send_to_crm(mocker):
    # Mock data
    user_data = UserData(user_id=1, name='test', document='12345678901', email="test@example.com", phone="1234567890")
    crm_settings = MockRequestResponse(
        value = {
        "url": "https://api.example.com",
        "access_key": "abc123",
        "deal_stage_id": "123",
        "deal_stage_name": "Abandoned Cart",
    })

    # Mock functions
    async def mock_get_settings(_, *, transaction):
        return crm_settings
    mock_requests_post = mocker.patch("requests.post", return_value = AsyncMock(status_code=200))

    # Act
    await send_abandonated_cart_to_crm(user_data, get_settings=mock_get_settings)

    # Assertions
    mock_requests_post.spy(
        "https://api.example.com/deals?token=abc123",
        json=mocker.ANY,
        headers=mocker.ANY,
        timeout=500,
    )
    assert user_data.email in mock_requests_post.call_args.kwargs["json"]["contacts"][0]["emails"][0]["email"]


@pytest.mark.asyncio()
async def test_send_to_crm_fails_with_bad_status_code(mocker):
    # Mock data
    user_data = UserData(user_id=1, name='test', document='12345678901', email="test@example.com", phone="1234567890")
    crm_settings = MockRequestResponse(
        value = {
        "url": "https://api.example.com",
        "access_key": "abc123",
        "deal_stage_id": "123",
        "deal_stage_name": "Abandoned Cart",
    })

    # Mock functions
    async def mock_get_settings(_, *, transaction):
        return crm_settings
    mock_requests_post = mocker.patch("requests.post", return_value = AsyncMock(status_code=400))

    # Act
    with pytest.raises(NotSendToCRMError):
        await send_abandonated_cart_to_crm(user_data, get_settings=mock_get_settings)

    # Assertions
    mock_requests_post.spy(
        "https://api.example.com/deals?token=abc123",
        json=mocker.ANY,
        headers=mocker.ANY,
        timeout=500,
    )


@pytest.mark.asyncio()
async def test_get_settings_raises_exception(mocker):
    # Mock data
    user_data = UserData(user_id=1, name='test', document='12345678901', email="test@example.com", phone="1234567890")

    # Mock functions (raises exception)
    async def mock_get_settings(_, *, transaction):
        return crm_settings

    with pytest.raises(Exception) as exc:
        await send_abandonated_cart_to_crm(user_data, get_settings=mock_get_settings)

    # Assertions
    assert exc

