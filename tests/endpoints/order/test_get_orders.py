from fastapi import status
from httpx import AsyncClient
from main import app
import pytest
from pytest_mock import MockerFixture

from tests.factories_db import OrderFactory, OrderStatusStepsFactory, UserDBFactory

URL = '/order'


@pytest.mark.asyncio
async def test_give_no_orders_should_return_empty_list() -> None:
    """Should return empty list."""
    # Act
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.get(
            f'{URL}/orders',
        )

    # Assert
    assert response.json().get('orders') == []
    assert response.status_code == status.HTTP_200_OK
    assert response.request.method == 'GET'


@pytest.mark.asyncio
async def test_get_all_orders(mocker: MockerFixture, db) -> None:
    """Should Return Orders."""
    # Arrange
    with db:
        user = UserDBFactory()
        db.add(user)
        db.flush()
        order = OrderFactory(user=user)
        db.add(order)
        db.flush()
        new_order_status_steps = OrderStatusStepsFactory(order=order)
        db.add(new_order_status_steps)
        db.commit()

    # Act
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.get(
            f'{URL}/orders',
        )

    # Assert
    assert response.json().get('orders')
    assert response.status_code == status.HTTP_200_OK
    assert response.request.method == 'GET'
