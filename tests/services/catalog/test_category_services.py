# ruff: noqa: I001
import pytest
from pytest_mock import MockerFixture

from app.catalog.services import (
    create_category,
    update_category,
    delete_category,
    get_category_by_id,
)
from app.entities.catalog import CategoryCreate, CategoryUpdate
from app.entities.category import CategoryNotFoundError
from tests.factories_db import CategoryFactory, CreditCardFeeConfigFactory


@pytest.mark.asyncio
async def test_create_category_should_return_category(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    category_data = CategoryCreate(
        name='Test Category',
        path='test-category',
        menu=True,
        showcase=False,
    )

    # Act
    result = await create_category(category_data, db=asyncdb)

    # Assert
    assert result.name == category_data.name
    assert result.path == category_data.path
    assert result.menu is True
    assert result.showcase is False


@pytest.mark.asyncio
async def test_get_category_by_id_should_return_category(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    # Act
    result = await get_category_by_id(category.category_id, db=asyncdb)

    # Assert
    assert result is not None
    assert result.category_id == category.category_id
    assert result.name == category.name
    assert result.path == category.path


@pytest.mark.asyncio
async def test_get_category_by_id_not_found_should_return_none(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act
    result = await get_category_by_id(999, db=asyncdb)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_category_should_return_updated_category(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    update_data = CategoryUpdate(
        name='Updated Category',
        menu=True,
    )

    # Act
    result = await update_category(category.category_id, update_data, db=asyncdb)

    # Assert
    assert result is not None
    assert result.name == 'Updated Category'
    assert result.menu is True


@pytest.mark.asyncio
async def test_update_category_not_found_should_return_none(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    update_data = CategoryUpdate(name='Updated Category')

    # Act
    with pytest.raises(CategoryNotFoundError):
        await update_category(999, update_data, db=asyncdb)


@pytest.mark.asyncio
async def test_delete_category_should_delete_category(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        category = CategoryFactory()
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add_all([category, config_fee])
        await transaction.session.commit()

    # Act
    await delete_category(category.category_id, db=asyncdb)

    # Assert
    result = await get_category_by_id(category.category_id, db=asyncdb)
    assert result is None


@pytest.mark.asyncio
async def test_delete_category_not_found_should_raise_exception(asyncdb):
    # Setup
    async with asyncdb().begin() as transaction:
        config_fee = CreditCardFeeConfigFactory()
        transaction.session.add(config_fee)
        await transaction.session.commit()

    # Act
    with pytest.raises(CategoryNotFoundError):
        await delete_category(999, db=asyncdb)
