from decimal import Decimal
from uuid import UUID
import pytest
from pytest_mock import MockerFixture
from app.entities.cart import CartBase

from app.entities.product import ProductCart
from app.cart.services import add_product_to_cart, calculate_cart
from app.infra.bootstrap import Command
from app.infra.redis import MemoryCache
from tests.fake_functions import fake


@pytest.mark.asyncio()
async def test_add_product_to_new_cart(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to new cart and return cart_id."""
    # Arrange
    product = ProductCart(
        product_id=1,
        quantity=1,
    )
    bootstrap = await memory_bootstrap

    # Act
    cart_response = await add_product_to_cart(None, product, bootstrap)

    # Assert
    assert cart_response.uuid
    assert len(cart_response.cart_items) == 1
    assert isinstance(cart_response.uuid, UUID)
    assert cart_response.cart_items[0].product_id == product.product_id
    assert cart_response.cart_items[0].quantity == product.quantity


@pytest.mark.asyncio()
async def test_add_product_to_new_cart_should_set_in_cache(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to new cart and set cart in cache."""
    # Arrange
    product = ProductCart(
        product_id=1,
        quantity=1,
    )
    bootstrap = await memory_bootstrap
    cache_spy = mocker.spy(bootstrap.cache, 'set')

    # Act
    cart_response = await add_product_to_cart(None, product, bootstrap)

    # Assert
    cache_spy.assert_called_once_with(
        str(cart_response.uuid),
        cart_response.model_dump_json(),
    )


@pytest.mark.asyncio()
async def test_add_product_to_current_cart_should_add_new_product_should_calculate_subtotal(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to current cart and calc subtotal."""
    # Arrange
    current_product = ProductCart(
        product_id=2,
        quantity=1,
    )
    new_product = ProductCart(
        product_id=1,
        quantity=1,
    )
    bootstrap = await memory_bootstrap
    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=[current_product],
        subtotal=Decimal(10),
    )
    cache = bootstrap.cache
    cache.set(str(uuid), cart.model_dump_json())

    # Act
    cart_response = await add_product_to_cart(
        str(uuid),
        new_product,
        bootstrap,
    )

    # Assert
    assert str(cart_response.uuid) == str(uuid)
    assert cart_response.cart_items[0].product_id == current_product.product_id
    assert cart_response.cart_items[0].quantity == current_product.quantity
    assert cart_response.cart_items[1].product_id == new_product.product_id
    assert cart_response.cart_items[1].quantity == new_product.quantity


@pytest.mark.asyncio()
async def test_given_cart_with_items_need_calculate_to_preview(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to current cart and calc subtotal."""
    # Arrange
    cart_items = []
    first_product = ProductCart(
        product_id=2,
        quantity=1,
    )
    second_product = ProductCart(
        product_id=1,
        quantity=1,
    )
    cart_items.append(first_product)
    cart_items.append(second_product)
    bootstrap = await memory_bootstrap
    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=cart_items,
        coupon='code',
        subtotal=Decimal(10),
    )
    cache = bootstrap.cache
    cache.set(str(uuid), cart.model_dump_json())

    # Act
    cart_response = await calculate_cart(
        uuid=str(uuid),
        cart=cart,
        bootstrap=bootstrap,
    )

    # Assert
    assert str(cart_response.uuid) == str(uuid)
