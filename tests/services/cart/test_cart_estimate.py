from unittest.mock import AsyncMock, Mock
from uuid import UUID
import pytest
from pytest_mock import MockerFixture
from app.cart.services import add_product_to_cart, calculate_cart
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.database import get_async_session
from tests.factories_db import ProductDBFactory
from tests.services.cart.test_cart_step_1 import create_product_cart


@pytest.mark.asyncio()
async def test_estimate_cart_with_product(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Should return valid cart."""
    # Arrange
    product = create_product_cart()
    productdb = ProductDBFactory(product_id=1, discount=0)
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb,
    )
    bootstrap.cache = Mock()
    bootstrap.db = get_async_session()
    cart_response = await add_product_to_cart(None, product, bootstrap)
    mocker.patch.object(
        bootstrap.cache,
        'get',
        return_value=cart_response.model_dump_json(),
    )
    mocker.patch.object(
        bootstrap.cart_repository, 'get_products', return_value=[productdb]
    )
    product_quantity = productdb
    product_quantity.quantity = 10
    mocker.patch.object(
        bootstrap.cart_repository,
        'get_products_quantity',
        return_value=[product_quantity.__dict__],
    )

    # Act
    tt = await calculate_cart(
        uuid=cart_response.uuid, cart=cart_response, bootstrap=bootstrap
    )

    # Assert
    assert cart_response.uuid
    assert len(cart_response.cart_items) == 1
    assert isinstance(cart_response.uuid, UUID)
    assert cart_response.cart_items[0].product_id == product.product_id
    assert cart_response.cart_items[0].quantity == product.quantity
