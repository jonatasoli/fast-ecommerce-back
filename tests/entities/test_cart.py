from uuid import UUID

from app.entities.cart import CartBase, generate_cart_uuid
from app.entities.product import ProductCart
from tests.fake_functions import fake, fake_decimal

DEFAULT_PRODUCT_ID = 1


def test_create_uuid_to_cart() -> None:
    """Must return a UUID."""
    # Act
    uuid = generate_cart_uuid()

    # Assert
    assert isinstance(uuid, UUID)


def create_cart(product_id: int = DEFAULT_PRODUCT_ID) -> CartBase:
    """Generate random shopping cart."""
    return CartBase(
        uuid=fake.uuid4(),
        cart_items=[
            ProductCart(
                product_id=product_id,
                quantity=fake.random_int(),
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
