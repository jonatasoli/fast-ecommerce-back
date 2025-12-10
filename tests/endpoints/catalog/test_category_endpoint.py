from fastapi import status
from app.infra.database import get_async_session
from main import app
from httpx import ASGITransport, AsyncClient
import pytest

from tests.factories_db import (
    CategoryFactory,
    CreditCardFeeConfigFactory,
    UserDBFactory,
    RoleDBFactory,
)


URL_BASE = '/catalog/category'


@pytest.mark.asyncio
async def test_get_category_by_id_should_return_200(asyncdb, admin_token):
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
            f'{URL_BASE}/{category.category_id}',
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('category_id') == category.category_id
    assert response.json().get('name') == category.name
    assert response.json().get('path') == category.path


@pytest.mark.asyncio
async def test_get_category_by_id_not_found_should_return_404(asyncdb):
    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.get(
            f'{URL_BASE}/999',
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_category_should_return_201(asyncdb, admin_token):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    category_data = {
        'name': 'Test Category',
        'path': 'test-category',
        'menu': True,
        'showcase': False,
    }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            URL_BASE,
            json=category_data,
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json().get('name') == category_data['name']
    assert response.json().get('path') == category_data['path']
    assert response.json().get('menu') is True
    assert response.json().get('showcase') is False


@pytest.mark.asyncio
async def test_create_category_without_auth_should_return_401(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    category_data = {
        'name': 'Test Category',
        'path': 'test-category',
    }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            URL_BASE,
            json=category_data,
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_create_category_invalid_data_should_return_422(asyncdb, admin_token):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    category_data = {
        'name': 'Test Category',
    }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.post(
            URL_BASE,
            json=category_data,
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_update_category_should_return_200(asyncdb, admin_token):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    update_data = {
        'name': 'Updated Category',
        'menu': True,
    }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.patch(
            f'{URL_BASE}/{category.category_id}',
            json=update_data,
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get('name') == update_data['name']
    assert response.json().get('menu') is True


@pytest.mark.asyncio
async def test_update_category_not_found_should_return_404(asyncdb, admin_token):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    update_data = {
        'name': 'Updated Category',
    }

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.patch(
            f'{URL_BASE}/999',
            json=update_data,
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_category_should_return_204(asyncdb, admin_token):
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
        response = await client.delete(
            f'{URL_BASE}/{category.category_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_category_not_found_should_return_404(asyncdb, admin_token):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url='http://test',
    ) as client:
        app.dependency_overrides[get_async_session] = lambda: asyncdb
        response = await client.delete(
            f'{URL_BASE}/999',
            headers={'Authorization': f'Bearer {admin_token}'},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
