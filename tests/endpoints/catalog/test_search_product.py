# ruff: noqa: I001
from fastapi import status
from app.infra.database import get_async_session
from main import app
from httpx import ASGITransport, AsyncClient
import pytest

from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    InventoryDBFactory,
    ProductDBFactory,
)


URL = '/catalog/'


@pytest.mark.asyncio
async def test_empty_data_should_return_200(asyncdb):
    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            URL,
            params={'offset': 1, 'page': 1, 'search': ''},
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_with_product_list_only_activated(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.flush()
        product_db_1 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=100,
            active=True,
        )
        product_db_2 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=200,
            active=False,
        )

        transaction.session.add_all([product_db_1, product_db_2])
        await transaction.session.flush()

        inventory_db_1 = InventoryDBFactory(
            product=product_db_1,
            inventory_id=1,
        )
        inventory_db_2 = InventoryDBFactory(
            product=product_db_2,
            inventory_id=2,
        )
        transaction.session.add_all([inventory_db_1, inventory_db_2])
        await transaction.session.commit()

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            URL,
            params={'offset': 1, 'page': 1, 'search': f'{product_db_1.name}'},
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json().get('products')[0].get('product_id') == product_db_1.product_id
    )
