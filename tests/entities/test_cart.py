import pytest
from uuid import UUID
from decimal import Decimal

from app.entities.cart import (
    CartBase,
    CartNotFoundPriceError,
    generate_cart_uuid,
)
from app.entities.product import ProductCart
from app.entities.coupon import CouponCreate
from tests.fake_functions import fake, fake_decimal, fake_url_path

DEFAULT_PRODUCT_ID = fake.random_int()
DEFAULT_QUANTITY = fake.random_int()


def test_create_uuid_to_cart() -> None:
    """Must return a UUID."""
    # Act
    uuid = generate_cart_uuid()

    # Assert
    assert isinstance(uuid, UUID)


def create_cart(
    product_id: int = DEFAULT_PRODUCT_ID,
    quantity: int = DEFAULT_QUANTITY,
) -> CartBase:
    """Generate random shopping cart."""
    return CartBase(
        uuid=fake.uuid4(),
        cart_items=[
            ProductCart(
                product_id=product_id,
                name=None,
                image_path=None,
                quantity=quantity,
                price=fake_decimal(),
            ),
        ],
        subtotal=fake_decimal(),
    )


def test_create_base_cart() -> None:
    """Must create base cart."""
    # Arrange
    cart = create_cart()

    # Act/Assert
    assert cart is not None
    assert isinstance(cart, CartBase)
    assert isinstance(cart.uuid, UUID)


def test_increase_product_to_cart() -> None:
    """Must increase quantity in a product."""
    # Arrange
    product_id = fake.random_int()
    cart = create_cart(product_id=product_id)
    increase_quantity = cart.cart_items[0].quantity + 1

    # Act
    output = cart.increase_quantity(product_id=product_id)

    # Assert
    assert output.cart_items[0].quantity == increase_quantity


def test_decrease_product_to_cart() -> None:
    """Must decrease quantity in a product."""
    # Arrange
    product_id = fake.random_int()
    cart = create_cart(product_id=product_id)
    decrease_quantity = cart.cart_items[0].quantity - 1

    # Act
    output = cart.decrease_quantity(product_id=product_id)

    # Assert
    assert output.cart_items[0].quantity == decrease_quantity


def test_set_product_quantity_to_cart() -> None:
    """Must set quantity in a product."""
    # Arrange
    product_id = fake.random_int()
    cart = create_cart(product_id=product_id)
    quantity = fake.random_int()

    # Act
    output = cart.set_product_quantity(
        product_id=product_id,
        quantity=quantity,
    )

    # Assert
    assert output.cart_items[0].quantity == quantity


def test_add_product_to_cart() -> None:
    """Must add a product to cart."""
    # Arrange
    product_id = fake.random_int()
    cart = create_cart()

    # Act
    output = cart.add_product(
        name=None,
        image_path=None,
        product_id=product_id,
        quantity=1,
        price=fake_decimal(),
    )

    # Assert
    assert output.cart_items[1].product_id == product_id
    assert output.cart_items[1].quantity == 1


def test_add_duplicate_product_should_increase_quantity() -> None:
    """Must add a product to cart."""
    # Arrange
    product_id = fake.random_int()
    quantity = fake.random_int()
    cart = create_cart(product_id=product_id, quantity=quantity)
    increase_quantity = cart.cart_items[0].quantity + 1

    # Act
    output = cart.add_product(
        name=fake.name(),
        image_path=fake_url_path(),
        price=fake_decimal(),
        product_id=product_id,
        quantity=1,
    )

    # Assert
    assert output.cart_items[0].quantity == increase_quantity
    assert len(output.cart_items) == 1


def test_remove_product_to_cart() -> None:
    """Must remove a product to cart."""
    # Arrange
    product_id = fake.random_int()
    cart = create_cart(product_id=product_id)

    # Act
    output = cart.remove_product(product_id=product_id)

    # Assert
    assert output.cart_items == []


def test_remove_product_to_cart_with_product_not_exists() -> None:
    """Must remove a product to cart."""
    # Arrange
    product_id = 2
    cart = create_cart(product_id=1)

    # Act
    with pytest.raises(IndexError) as index_error:
        cart.remove_product(product_id=product_id)

    # Assert
    assert (
        index_error.value.args[0]
        == f"Product id {product_id} don't exists in cart"
    )


def test_add_product_price_to_cart() -> None:
    """Must add a product price to cart."""
    # Arrange
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=[],
        subtotal=Decimal(0),
    )
    list_product_prices = []
    for _ in range(10):
        product_name = fake.name()
        image_path = fake_url_path()
        product_id = fake.random_int()
        price = fake_decimal()
        quantity = fake.random_int()

        cart.cart_items.append(
            ProductCart(
                name=product_name,
                image_path=image_path,
                price=fake_decimal(),
                product_id=product_id,
                quantity=quantity,
            ),
        )
        list_product_prices.append(
            ProductCart(
                name=product_name,
                image_path=image_path,
                product_id=product_id,
                price=price,
                quantity=quantity,
            ),
        )

    # Act
    cart.add_product_price(list_product_prices)

    # Assert
    for index, _ in enumerate(range(10)):
        assert cart.cart_items[index].price == list_product_prices[index].price


def test_calculate_subtotal_to_cart() -> None:
    """Must calculate subtotal to cart."""
    # Arrange
    cart_items = []
    subtotal = 0
    for _ in range(10):
        price = fake_decimal()
        quantity = fake.random_int()
        cart_items.append(
            ProductCart(
                name=fake.name(),
                image_path=fake_url_path(),
                product_id=fake.random_int(),
                quantity=quantity,
                price=price,
            ),
        )
        subtotal += quantity * price
    cart = create_cart()
    cart.cart_items = cart_items

    # Act
    cart.calculate_subtotal()

    # Assert
    assert cart.subtotal == subtotal


def test_calculate_subtotal_in_cart_without_prices_raise_cart_error() -> None:
    """Must raise CartNotFoundPriceError."""
    # Arrange
    cart_items = []
    for _ in range(10):
        cart_items.append(
            ProductCart(
                name=fake.name(),
                image_path=fake_url_path(),
                product_id=fake.random_int(),
                quantity=fake.random_int(),
                price=None,
            ),
        )
    cart = create_cart()
    cart.cart_items = cart_items

    # Act
    with pytest.raises(CartNotFoundPriceError) as cnfpe_error:
        cart.calculate_subtotal()

    # Assert
    assert (
        cnfpe_error.value.args[0] == 'Price or quantity not found in cart item'
    )


def test_calculate_subtotal_in_cart_with_cart_items_empty_raise_value_error() -> None:
    """Must raise ValueError."""
    # Arrange
    cart = create_cart()
    cart.cart_items = []

    # Act/Assert
    with pytest.raises(ValueError, match='Cart items is empty'):
        cart.calculate_subtotal()


def test_calculate_subtotal_in_cart_with_coupon() -> None:
    """Must calculate subtotal to cart with coupon."""
    # Arrange
    cart_items = []
    subtotal = 0
    discount = 0
    discount_subtotal = 0
    discount_percentage = Decimal(
        fake.random_number(digits=2, fix_len=True) / 100,
    )
    coupon = CouponCreate(
        code=fake.word(),
        discount=discount_percentage,
    )
    for _ in range(10):
        price = fake_decimal()
        quantity = fake.random_int()
        cart_items.append(
            ProductCart(
                name=fake.name(),
                image_path=fake_url_path(),
                product_id=fake.random_int(),
                quantity=quantity,
                discount_price=Decimal('0'),
                price=price,
            ),
        )
        subtotal += quantity * price
        discount_price = price * discount_percentage
        discount += discount_price * quantity
    discount_subtotal += subtotal - discount
    cart = create_cart()
    cart.cart_items = cart_items
    cart.coupon = coupon.code

    # Act
    cart.calculate_subtotal(discount=coupon.discount)

    # Assert
    assert cart.subtotal == discount_subtotal
    assert cart.coupon == coupon.code
    assert cart.discount == discount
