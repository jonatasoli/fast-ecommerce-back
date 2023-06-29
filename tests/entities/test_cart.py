import pytest
from uuid import UUID

from app.entities.cart import CartBase, generate_cart_uuid
from app.entities.product import ProductCart
from tests.fake_functions import fake, fake_decimal

DEFAULT_PRODUCT_ID = fake.random_int()
DEFAULT_QUANTITY = fake.random_int()


def test_create_uuid_to_cart() -> None:
    """Must return a UUID."""
    # Act
    uuid = generate_cart_uuid()

    # Assert
    assert isinstance(uuid, UUID)


def create_cart(product_id: int = DEFAULT_PRODUCT_ID, quantity: int = DEFAULT_QUANTITY) -> CartBase:
    """Generate random shopping cart."""
    return CartBase(
        uuid=fake.uuid4(),
        cart_items=[
            ProductCart(
                product_id=product_id,
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
        product_id=product_id,
        quantity=1,
    )

    # Assert
    assert output.cart_items[1]["product_id"] == product_id
    assert output.cart_items[1]["quantity"] == 1


def test_add_duplicate_product_should_increase_quantity() -> None:
    """Must add a product to cart."""
    # Arrange
    product_id = fake.random_int()
    quantity = fake.random_int()
    cart = create_cart(product_id=product_id, quantity=quantity)
    increase_quantity = cart.cart_items[0].quantity + 1

    # Act
    output = cart.add_product(
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
    assert index_error.value.args[0] == f"Product id {product_id} don't exists in cart"


def test_calculate_subtotal_to_cart() -> None:
    ...


def test_caculate_subtotal_in_cart_without_prices() -> None:
    ...


def test_calculate_subtotal_in_cart_with_prices() -> None:
    ...


def test_calculate_subtotal_in_cart_with_cart_items_empty() -> None:
    ...
