import pytest
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.entities.cart import (
    CartBase,
    CartNotFoundPriceError,
    CartNotFoundError,
    InvalidCartFormatError,
    InvalidCartUUIDError,
    CheckoutProcessingError,
    CouponLimitPriceError,
    CartInconsistencyError,
    generate_cart_uuid,
    convert_price_to_decimal,
    generate_empty_cart,
    generate_new_cart,
    validate_cache_cart,
)
from app.entities.product import ProductCart, ProductNotFoundError
from tests.fake_functions import fake, fake_decimal
from tests.factories import (
    ProductCartFactory,
    ProductInDBFactory,
    CouponInDBFactory,
    FreightFactory,
)


def test_create_uuid_to_cart() -> None:
    # Act
    uuid = generate_cart_uuid()

    assert isinstance(uuid, UUID)


def test_create_base_cart() -> None:
    # Setup
    uuid = fake.uuid4()
    cart_items = [ProductCartFactory()]
    subtotal = fake_decimal()

    # Act
    cart = CartBase(uuid=uuid, cart_items=cart_items, subtotal=subtotal)

    assert cart is not None
    assert isinstance(cart, CartBase)
    assert isinstance(cart.uuid, UUID)


def test_increase_product_to_cart() -> None:
    # Setup
    product_id = fake.random_int()
    initial_quantity = fake.random_int(min=1, max=5)
    product = ProductCartFactory(product_id=product_id, quantity=initial_quantity)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    expected_quantity = initial_quantity + 1

    # Act
    output = cart.increase_quantity(product_id=product_id)

    assert output.cart_items[0].quantity == expected_quantity


def test_decrease_product_to_cart() -> None:
    # Setup
    product_id = fake.random_int()
    initial_quantity = fake.random_int(min=2, max=10)
    product = ProductCartFactory(product_id=product_id, quantity=initial_quantity)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    expected_quantity = initial_quantity - 1

    # Act
    output = cart.decrease_quantity(product_id=product_id)

    assert output.cart_items[0].quantity == expected_quantity


def test_set_product_quantity_to_cart() -> None:
    # Setup
    product_id = fake.random_int()
    new_quantity = fake.random_int(min=1, max=20)
    product = ProductCartFactory(product_id=product_id)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())

    # Act
    output = cart.set_product_quantity(product_id=product_id, quantity=new_quantity)

    assert output.cart_items[0].quantity == new_quantity


def test_add_product_to_cart() -> None:
    # Setup
    existing_product = ProductCartFactory()
    new_product_id = fake.random_int()
    new_price = fake_decimal()
    cart = CartBase(
        uuid=fake.uuid4(), cart_items=[existing_product], subtotal=fake_decimal(),
    )

    # Act
    output = cart.add_product(
        name=fake.name(),
        image_path=fake.uri_path(),
        product_id=new_product_id,
        quantity=1,
        price=new_price,
        available_quantity=fake.random_int(min=1, max=100),
    )

    assert len(output.cart_items) == 2
    assert output.cart_items[1].product_id == new_product_id
    assert output.cart_items[1].quantity == 1


def test_add_duplicate_product_should_increase_quantity() -> None:
    # Setup
    product_id = fake.random_int()
    initial_quantity = fake.random_int(min=1, max=5)
    product = ProductCartFactory(product_id=product_id, quantity=initial_quantity)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    expected_quantity = initial_quantity + 1

    # Act
    output = cart.add_product(
        name=fake.name(),
        image_path=fake.uri_path(),
        price=fake_decimal(),
        product_id=product_id,
        quantity=1,
        available_quantity=fake.random_int(min=10, max=100),
    )

    assert output.cart_items[0].quantity == expected_quantity
    assert len(output.cart_items) == 1


def test_remove_product_to_cart() -> None:
    # Setup
    product_id = fake.random_int()
    product = ProductCartFactory(product_id=product_id)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())

    # Act
    output = cart.remove_product(product_id=product_id)

    assert output.cart_items == []


def test_remove_product_to_cart_with_product_not_exists() -> None:
    # Setup
    product_id = fake.random_int()
    different_product_id = product_id + 1
    product = ProductCartFactory(product_id=product_id)
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())

    with pytest.raises(
        IndexError, match=f"Product id {different_product_id} don't exists in cart",
    ):
        cart.remove_product(product_id=different_product_id)


def test_add_product_price_to_cart() -> None:
    # Setup
    cart = CartBase(uuid=fake.uuid4(), cart_items=[], subtotal=Decimal(0))
    products_with_prices = []

    for _ in range(10):
        product_id = fake.random_int()
        price = fake_decimal()
        quantity = fake.random_int(min=1, max=5)

        cart.cart_items.append(
            ProductCartFactory(
                product_id=product_id, price=fake_decimal(), quantity=quantity,
            ),
        )

        products_with_prices.append(
            ProductCartFactory(product_id=product_id, price=price, quantity=quantity),
        )

    # Act
    cart.add_product_price(products_with_prices)

    for index, product in enumerate(products_with_prices):
        assert cart.cart_items[index].price == product.price


def test_calculate_subtotal_to_cart() -> None:
    # Setup
    cart_items = []
    expected_subtotal = Decimal(0)

    for _ in range(10):
        price = fake_decimal(min_value=10, max_value=100)
        quantity = fake.random_int(min=1, max=5)
        cart_items.append(ProductCartFactory(price=price, quantity=quantity))
        expected_subtotal += quantity * price

    cart = CartBase(uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0))

    # Act
    cart.calculate_subtotal(coupon=None)

    assert cart.subtotal == expected_subtotal


def test_calculate_subtotal_in_cart_without_prices_raise_cart_error() -> None:
    # Setup
    cart_items = [ProductCartFactory(price=None) for _ in range(10)]
    cart = CartBase(uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0))

    with pytest.raises(
        CartNotFoundPriceError, match='Price or quantity not found in cart item',
    ):
        cart.calculate_subtotal()


def test_calculate_subtotal_in_cart_with_cart_items_empty_raise_value_error() -> None:
    # Setup
    cart = CartBase(uuid=fake.uuid4(), cart_items=[], subtotal=Decimal(0))

    with pytest.raises(ValueError, match='Cart items is empty'):
        cart.calculate_subtotal()


def test_calculate_subtotal_in_cart_with_coupon() -> None:
    # Setup
    discount_percentage = Decimal(fake.random_number(digits=2, fix_len=True) / 100)
    coupon = CouponInDBFactory(
        discount=discount_percentage, discount_price=Decimal(0), limit_price=None,
    )

    cart_items = []
    expected_subtotal = Decimal(0)
    expected_discount = Decimal(0)

    for _ in range(10):
        price = fake_decimal(min_value=10, max_value=100)
        quantity = fake.random_int(min=1, max=5)
        cart_items.append(
            ProductCartFactory(
                price=price, quantity=quantity, discount_price=Decimal('0'),
            ),
        )
        expected_subtotal += quantity * price
        discount_price = price * discount_percentage
        expected_discount += discount_price * quantity

    expected_final_subtotal = expected_subtotal - expected_discount
    cart = CartBase(
        uuid=fake.uuid4(),
        cart_items=cart_items,
        subtotal=Decimal(0),
        coupon=coupon.code,
    )

    # Act
    cart.calculate_subtotal(coupon=coupon)

    assert cart.subtotal == expected_final_subtotal
    assert cart.coupon == coupon.code
    assert cart.discount == expected_discount


def test_cart_not_found_error_message():
    with pytest.raises(CartNotFoundError, match='Cart not found'):
        raise CartNotFoundError


def test_invalid_cart_format_error_message():
    with pytest.raises(InvalidCartFormatError, match='Invalid cart format'):
        raise InvalidCartFormatError


def test_invalid_cart_uuid_error_message():
    with pytest.raises(
        InvalidCartUUIDError, match='Cart uuid is not the same as the cache uuid',
    ):
        raise InvalidCartUUIDError


def test_checkout_processing_error_message():
    with pytest.raises(CheckoutProcessingError, match='Checkout error processing'):
        raise CheckoutProcessingError


def test_coupon_limit_price_error_message():
    with pytest.raises(
        CouponLimitPriceError, match='The price limit is below for the subototal',
    ):
        raise CouponLimitPriceError


def test_cart_inconsistency_error_message():
    with pytest.raises(
        CartInconsistencyError, match='Cart is diferent to product list to check',
    ):
        raise CartInconsistencyError


def test_increase_quantity_when_product_not_found_returns_cart():
    product = ProductCartFactory()
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    original_quantity = cart.cart_items[0].quantity
    non_existent_id = fake.random_int()

    result = cart.increase_quantity(product_id=non_existent_id)

    assert result == cart
    assert cart.cart_items[0].quantity == original_quantity


def test_decrease_quantity_when_product_not_found_returns_cart():
    product = ProductCartFactory()
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    original_quantity = cart.cart_items[0].quantity
    non_existent_id = fake.random_int()

    result = cart.decrease_quantity(product_id=non_existent_id)

    assert result == cart
    assert cart.cart_items[0].quantity == original_quantity


def test_set_product_quantity_when_product_not_found_returns_cart():
    product = ProductCartFactory()
    cart = CartBase(uuid=fake.uuid4(), cart_items=[product], subtotal=fake_decimal())
    original_quantity = cart.cart_items[0].quantity
    non_existent_id = fake.random_int()

    result = cart.set_product_quantity(product_id=non_existent_id, quantity=10)

    assert result == cart
    assert cart.cart_items[0].quantity == original_quantity


def test_calculate_subtotal_with_coupon_limit_price_error():
    subtotal_value = fake_decimal(min_value=10, max_value=50)
    limit_price_value = fake_decimal(min_value=100, max_value=200)

    cart_items = [ProductCartFactory(price=subtotal_value, quantity=1)]
    coupon = CouponInDBFactory(
        discount=Decimal('0'),
        discount_price=fake_decimal(min_value=5, max_value=20),
        limit_price=limit_price_value,
    )
    cart = CartBase(uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0))

    with pytest.raises(CouponLimitPriceError):
        cart.calculate_subtotal(coupon=coupon)


def test_calculate_subtotal_with_coupon_discount_price_success():
    discount_value = fake_decimal(min_value=10, max_value=30)
    price = fake_decimal(min_value=100, max_value=150)
    quantity = fake.random_int(min=2, max=5)
    limit_price = fake_decimal(min_value=50, max_value=99)

    cart_items = [ProductCartFactory(price=price, quantity=quantity)]
    coupon = CouponInDBFactory(
        discount=Decimal('0'),
        discount_price=discount_value,
        limit_price=limit_price,
    )
    cart = CartBase(uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0))

    cart.calculate_subtotal(coupon=coupon)

    assert cart.discount == discount_value
    assert cart.subtotal == (price * quantity) - discount_value


def test_calculate_subtotal_with_freight():
    price = fake_decimal(min_value=50, max_value=150)
    quantity = fake.random_int(min=1, max=5)
    freight_price = fake_decimal(min_value=10, max_value=50)

    cart_items = [ProductCartFactory(price=price, quantity=quantity)]
    freight = FreightFactory(price=freight_price)
    cart = CartBase(
        uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0), freight=freight,
    )

    cart.calculate_subtotal()

    assert cart.total == (price * quantity) + freight_price


def test_get_products_price_and_discounts_with_inconsistency():
    cart_items = [
        ProductCartFactory(product_id=fake.random_int()),
        ProductCartFactory(product_id=fake.random_int()),
    ]
    products = [ProductInDBFactory()]
    cart = CartBase(uuid=fake.uuid4(), cart_items=cart_items, subtotal=Decimal(0))

    with pytest.raises(CartInconsistencyError):
        cart.get_products_price_and_discounts(products)


def test_convert_price_to_decimal():
    int_price = fake.random_int(min=1000, max=100000)
    result = convert_price_to_decimal(int_price)

    expected = Decimal(int_price / 100)
    assert result == expected


def test_generate_empty_cart():
    cart = generate_empty_cart()

    assert isinstance(cart.uuid, UUID)
    assert cart.cart_items == []
    assert cart.subtotal == Decimal(0)


def test_generate_new_cart_with_product():
    product = ProductInDBFactory()
    price = fake_decimal(min_value=10, max_value=500)
    quantity = fake.random_int(min=1, max=10)
    available_quantity = fake.random_int(min=10, max=100)

    cart = generate_new_cart(
        product, price=price, quantity=quantity, available_quantity=available_quantity,
    )

    assert isinstance(cart.uuid, UUID)
    assert len(cart.cart_items) == 1
    assert cart.cart_items[0].product_id == product.product_id
    assert cart.subtotal == price * quantity


def test_generate_new_cart_without_product_raises_error():
    with pytest.raises(ProductNotFoundError):
        generate_new_cart(None, price=fake_decimal(), quantity=1, available_quantity=10)


def test_validate_cache_cart_with_none_raises_error():
    with pytest.raises(CartNotFoundError):
        validate_cache_cart(None)


def test_validate_cache_cart_with_non_bytes_raises_error():
    with pytest.raises(InvalidCartFormatError):
        validate_cache_cart(fake.word())


def test_validate_cache_cart_with_invalid_json_raises_error():
    with pytest.raises(InvalidCartFormatError):
        validate_cache_cart(b'invalid json{{{')
