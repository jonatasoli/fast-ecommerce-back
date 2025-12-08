# ruff: noqa: I001
from fastapi import status
from app.infra.database import get_async_session
from main import app
from httpx import ASGITransport, AsyncClient
import pytest

from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory


URL = '/catalog/categories'


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
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_with_categories_list(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            URL,
        )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json().get('categories')[0].get('category_id') == category.category_id
    )
