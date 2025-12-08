from fastapi import status
from httpx import ASGITransport, AsyncClient
from app.infra.database import get_session
from main import app
import pytest

from tests.factories_db import OrderFactory, OrderStatusStepsFactory, UserDBFactory

URL = '/order'


@pytest.mark.asyncio
async def test_give_no_orders_should_return_empty_list(db) -> None:
    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_session] = lambda: db
        response = await client.get(
            f'{URL}/orders',
        )

    # Assert
    assert response.json().get('orders') == []
    assert response.status_code == status.HTTP_200_OK
    assert response.request.method == 'GET'


@pytest.mark.asyncio
async def test_get_all_orders(db) -> None:
    # Setup
    with db().begin() as transaction:
        user = UserDBFactory()
        transaction.session.add(user)
        transaction.session.flush()
        order = OrderFactory(user=user)
        transaction.session.add(order)
        transaction.session.flush()
        new_order_status_steps = OrderStatusStepsFactory(order=order)
        transaction.session.add(new_order_status_steps)
        transaction.session.commit()

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_session] = lambda: db
        response = await client.get(
            f'{URL}/orders',
        )

    # Assert
    assert response.json().get('orders')
    assert response.status_code == status.HTTP_200_OK
    assert response.request.method == 'GET'
