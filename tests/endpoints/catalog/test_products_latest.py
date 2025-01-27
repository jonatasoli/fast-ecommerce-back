
from fastapi import status
from app.infra.database import get_async_session
from main import app
from httpx import ASGITransport, AsyncClient
import pytest

from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory, InventoryDBFactory, ProductDBFactory


URL = '/catalog/latest'


@pytest.mark.asyncio
async def test_empty_data_should_return_200(asyncdb):
    """Must return empty list."""
    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test') as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            URL,
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_with_product_list_only_last_product(asyncdb):
    """Must return with activate is true."""
    # Arrange
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
        transaction.session.add(product_db_1)
        await transaction.session.flush()

        product_db_2 = ProductDBFactory(
            category=category,
            installment_config=config_fee,
            price=200,
            active=True,
        )

        inventory_db_1 = InventoryDBFactory(
            product=product_db_1,
            product_id=1,
            inventory_id=1,
        )
        inventory_db_2 = InventoryDBFactory(
            product=product_db_2,
            product_id=2,
            inventory_id=2,
        )
        transaction.session.add(product_db_2)
        await transaction.session.flush()
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
            params={"offset": 1, "page": 1 },
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('products')[0].get('product_id') == product_db_2.product_id


