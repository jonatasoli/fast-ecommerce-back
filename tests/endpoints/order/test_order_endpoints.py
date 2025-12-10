import pytest
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.entities.order import (
    OrderInDB,
    OrderUserListResponse,
    OrderSchema,
    CancelOrder,
)
from app.entities.user import UserInDB
from app.infra.constants import OrderStatus
from tests.factories import UserDataFactory
from tests.fake_functions import fake, fake_decimal


@pytest.mark.asyncio
async def test_get_orders(async_client, mocker):
    # Setup
    mock_orders = []
    mocker.patch('app.order.services.get_orders', return_value=mock_orders)

    # Act
    response = await async_client.get('/order/orders')

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_user_order(async_client, mocker):
    # Setup
    mock_orders = []
    mocker.patch('app.order.services.get_user_order', return_value=mock_orders)

    # Act
    response = await async_client.get('/order/user/1')

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_order(async_client, mocker):
    # Setup
    user_data = UserDataFactory()
    mock_user = UserInDB(
        user_id=user_data.user_id,
        name=user_data.name,
        email=user_data.email,
        document=user_data.document,
        phone=user_data.phone,
        role_id=1,
        password='hashed',
    )
    mock_order = OrderInDB(
        order_id=fake.pyint(min_value=1, max_value=1000),
        user=mock_user,
        customer_id=str(user_data.user_id),
        order_date=datetime.now(UTC),
        order_status=OrderStatus.PAYMENT_PENDING.value,
        discount=fake_decimal(),
        items=[],
        affiliate_id=None,
        tracking_number=None,
        freight=None,
        coupon_id=None,
    )
    mocker.patch('app.order.services.get_order', return_value=mock_order)

    # Act
    response = await async_client.get(f'/order/{mock_order.order_id}')

    assert response.status_code == 200
    assert response.json()['order_id'] == mock_order.order_id


@pytest.mark.asyncio
async def test_create_order(async_client, mocker):
    # Setup
    mocker.patch('app.order.services.create_order', return_value=None)
    payload = {
        'order_id': fake.pyint(min_value=1, max_value=1000),
        'customer_id': fake.pyint(min_value=1, max_value=1000),
        'order_date': datetime.now(UTC).isoformat(),
        'tracking_number': fake.pystr(),
        'payment_id': fake.pyint(min_value=1, max_value=1000),
        'order_status': OrderStatus.PAYMENT_PENDING.value,
        'last_updated': datetime.now(UTC).isoformat(),
    }

    # Act
    response = await async_client.post('/order/create_order', json=payload)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_order(async_client, mocker):
    # Setup
    mocker.patch('app.order.services.delete_order', return_value=None)
    cancel_reason = fake.text(max_nb_chars=100)
    payload = {'cancel_reason': cancel_reason}

    # Act
    response = await async_client.request('DELETE', '/order/1', json=payload)

    assert response.status_code == 204
