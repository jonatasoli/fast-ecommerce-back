from decimal import Decimal
from unittest.mock import Mock
from uuid import UUID
import pytest
from pytest_mock import MockerFixture
from app.entities.cart import CartBase

from app.entities.product import ProductCart
from app.cart.services import add_product_to_cart, calculate_cart
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.database import get_async_session
from tests.factories_db import ProductDBFactory
from tests.fake_functions import fake, fake_url_path


def create_product_cart(
    product_id: int = 1,
    quantity: int = 1,
    discount_price: Decimal = Decimal(0),
) -> ProductCart:
    """Must create product in db."""
    return ProductCart(
        name=fake.name(),
        image_path=fake_url_path(),
        product_id=product_id,
        quantity=quantity,
        discount_price=discount_price,
    )


@pytest.mark.asyncio()
async def test_add_product_to_new_cart(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to new cart and return cart_id."""
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
    product = create_product_cart()
    productdb = ProductDBFactory(product_id=1, discount=0)
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb,
    )
    bootstrap.cache = Mock()
    cache_spy = mocker.spy(bootstrap.cache, 'set')

    # Act
    cart_response = await add_product_to_cart(None, product, bootstrap)

    # Assert
    cache_spy.assert_called_once_with(
        str(cart_response.uuid),
        cart_response.model_dump_json(),
        ex=600000,
    )


@pytest.mark.asyncio()
async def test_add_product_to_current_cart_should_add_new_product_should_calculate_subtotal(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to current cart and calc subtotal."""
    # Arrange
    current_product = create_product_cart(
        product_id=2,
        quantity=1,
    )
    new_product = create_product_cart(
        product_id=1,
        quantity=1,
    )

    productdb = ProductDBFactory(product_id=1, discount=0)
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb,
    )
    bootstrap.cache = Mock()
    mocker.spy(bootstrap.cache, 'set')

    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=[current_product],
        subtotal=Decimal(10),
    )

    mocker.patch.object(
        bootstrap.cache,
        'get',
        return_value=cart.model_dump_json(),
    )

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
async def test_given_cart_with_items_with_discount_need_calculate_to_preview(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Must add product to current cart and calc subtotal."""
    # Arrange
    cart_items = []
    first_product = create_product_cart(
        product_id=2,
        quantity=1,
        discount_price=Decimal('50'),
    )
    second_product = create_product_cart(
        product_id=1,
        quantity=1,
        discount_price=Decimal('50'),
    )
    cart_items.append(first_product)
    cart_items.append(second_product)

    productdb_1 = ProductDBFactory(
        product_id=1,
        discount=Decimal('50'),
        price=Decimal('100'),
        category_id=1,
        showcase=False,
        show_discount=False,
    )
    productdb_2 = ProductDBFactory(
        product_id=2,
        discount=Decimal('50'),
        price=Decimal('100'),
        category_id=1,
        showcase=False,
        show_discount=False,
    )

    bootstrap = await memory_bootstrap
    bootstrap.db = get_async_session()
    bootstrap.cache = Mock()
    product_inventory_1 = productdb_1
    product_inventory_2 = productdb_2
    product_inventory_1.quantity = 100
    product_inventory_2.quantity = 100

    async def async_mock(*args, **kwargs) -> list:
        return [
            product_inventory_1,
            product_inventory_2,
        ]

    mocker.patch.object(
        bootstrap.cart_repository,
        'get_products_quantity',
        side_effect=async_mock,
    )

    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=cart_items,
        subtotal=Decimal(10),
    )
    mocker.patch.object(
        bootstrap.cache,
        'get',
        return_value=cart.model_dump_json(),
    )

    # Act
    cart_response = await calculate_cart(
        uuid=str(uuid),
        cart=cart,
        bootstrap=bootstrap,
    )

    # Assert
    assert str(cart_response.uuid) == str(uuid)
    assert cart_response.subtotal == Decimal('100')
    assert cart_response.discount == Decimal('100')
