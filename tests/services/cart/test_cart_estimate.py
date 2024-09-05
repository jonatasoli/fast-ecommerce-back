from decimal import Decimal
from unittest.mock import Mock
from uuid import UUID
import pytest
from pytest_mock import MockerFixture
from app.cart.services import calculate_cart
from app.entities.cart import CartBase
from app.infra.bootstrap.cart_bootstrap import Command
from app.infra.database import get_async_session
from tests.factories_db import CouponFactory, ProductDBFactory
from tests.services.cart.test_cart_step_1 import create_product_cart

from tests.fake_functions import fake


@pytest.mark.asyncio
async def test_estimate_cart_with_product(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None: """Should return valid cart.""" # Arrange cart_items = [] product_1 = create_product_cart()
    product_2 = create_product_cart(product_id=2)
    cart_items.append(product_1)
    cart_items.append(product_2)

    productdb_1 = ProductDBFactory(product_id=1, discount=0)
    productdb_2 = ProductDBFactory(product_id=2, discount=0)
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb_1,
    )
    bootstrap.cache = Mock()
    bootstrap.db = get_async_session()

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

    product_quantity_1 = productdb_1
    product_quantity_1.quantity = 10
    product_quantity_2 = productdb_2
    product_quantity_2.quantity = 10
    subtotal = productdb_1.price + productdb_2.price
    discount = productdb_1.discount + productdb_2.discount
    mocker.patch.object(
        bootstrap.cart_repository,
        'get_products_quantity',
        return_value=[
            product_quantity_1,
            product_quantity_2,
        ],
    )

    # Act
    cart_response = await calculate_cart(
        uuid=cart.uuid,
        cart=cart,
        bootstrap=bootstrap,
    )

    # Assert
    assert cart.uuid
    assert len(cart.cart_items) == 2
    assert isinstance(cart.uuid, UUID)
    assert cart_response.subtotal == subtotal
    assert cart_response.discount == discount


@pytest.mark.asyncio
async def test_estimate_cart_with_coupon_discount(
    memory_bootstrap: Command,
    mocker: MockerFixture,
) -> None:
    """Should return valid cart."""
    # Arrange
    cart_items = []
    product_1 = create_product_cart()
    product_2 = create_product_cart(product_id=2)
    cart_items.append(product_1)
    cart_items.append(product_2)
    coupon = CouponFactory(code='D10', discount=Decimal('0.1'))

    productdb_1 = ProductDBFactory(product_id=1, discount=Decimal('0'))
    productdb_2 = ProductDBFactory(product_id=2, discount=Decimal('0'))
    bootstrap = await memory_bootstrap
    mocker.patch.object(
        bootstrap.uow,
        'get_product_by_id',
        return_value=productdb_1,
    )
    bootstrap.cache = Mock()
    bootstrap.db = get_async_session()

    uuid = fake.uuid4()
    cart = CartBase(
        uuid=uuid,
        cart_items=cart_items,
        subtotal=Decimal(10),
        coupon=coupon.code,
    )
    mocker.patch.object(
        bootstrap.cache,
        'get',
        return_value=cart.model_dump_json(),
    )

    mocker.patch.object(
        bootstrap.cart_repository,
        'get_coupon_by_code',
        return_value=coupon,
    )
    product_quantity_1 = productdb_1
    product_quantity_1.quantity = 10
    product_quantity_2 = productdb_2
    product_quantity_2.quantity = 10
    subtotal = productdb_1.price + productdb_2.price
    discount = subtotal * coupon.discount
    subtotal = subtotal - discount
    mocker.patch.object(
        bootstrap.cart_repository,
        'get_products_quantity',
        return_value=[
            product_quantity_1,
            product_quantity_2,
        ],
    )

    # Act
    cart_response = await calculate_cart(
        uuid=cart.uuid,
        cart=cart,
        bootstrap=bootstrap,
    )

    # Assert
    assert cart.uuid
    assert len(cart.cart_items) == 2
    assert isinstance(cart.uuid, UUID)
    assert cart_response.subtotal == subtotal
    assert cart_response.discount == discount
