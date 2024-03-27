from unittest.mock import Mock
import pytest
from pytest_mock import MockerFixture
from app.cart.services import add_product_to_cart
from app.infra.bootstrap.cart_bootstrap import Command
from tests.factories_db import ProductDBFactory


@pytest.mark.skip()
async def test_estimate_cart_with_product(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Should return valid cart."""
    # Arrange
    productdb = ProductDBFactory(product_id=1, discount=0)
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb,
    )
    bootstrap.cache = Mock()

    # Act
    cart_response = await add_product_to_cart(None, product, bootstrap)

    # Assert
    assert cart_response.uuid
    assert len(cart_response.cart_items) == 1
    assert isinstance(cart_response.uuid, UUID)
    assert cart_response.cart_items[0].product_id == product.product_id
    assert cart_response.cart_items[0].quantity == product.quantity
