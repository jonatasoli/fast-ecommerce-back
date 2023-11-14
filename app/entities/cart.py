import json
from decimal import Decimal
from typing import Self
from uuid import UUID, uuid4
from loguru import logger


from app.entities.freight import ShippingAddress
from app.entities.product import ProductCart, ProductInDB
from app.entities.user import UserAddress, UserData
from pydantic import BaseModel

from app.freight.entities import Freight


class CartNotFoundPriceError(Exception):
    """Raise when cart not found price."""

    def __init__(self: Self) -> None:
        super().__init__('Price or quantity not found in cart item')


class ProductNotFoundError(Exception):
    """Raise when gived product not exists in database."""

    def __init__(self: Self) -> None:
        super().__init__('Product not found in database')


class CartInconsistencyError(Exception):
    """Raise when cart is diferent to product list to check."""

    def __init__(self: Self) -> None:
        super().__init__('Cart is diferent to product list to check')


class CartNotFoundError(Exception):
    """Raise when cart not found."""

    def __init__(self: Self) -> None:
        super().__init__('Cart not found')


class InvalidCartFormatError(Exception):
    """Raise when cart is invalid."""

    def __init__(self: Self) -> None:
        super().__init__('Invalid cart format')


def generate_cart_uuid() -> UUID:
    """Generate UUID to Cart."""
    return uuid4()


class CartBase(BaseModel):
    """Cart first step representation."""

    uuid: UUID
    affiliate: str | None = None
    cart_items: list[ProductCart | None] = []
    coupon: str | None = None
    discount: Decimal = Decimal(0)
    zipcode: str | None = None
    freight_product_code: str | None = None
    freight: Freight | None = None
    subtotal: Decimal
    total: Decimal = Decimal(0)

    def increase_quantity(self: Self, product_id: int) -> Self:
        """Increase quantity in a product."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.quantity += 1
            return self
        return self

    def decrease_quantity(self: Self, product_id: int) -> Self:
        """Decrease quantity in a product."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.quantity -= 1
            return self
        return self

    def set_product_quantity(
        self: Self,
        product_id: int,
        quantity: int,
    ) -> Self:
        """Set quantity in a product."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.quantity = quantity
            return self
        return self

    def add_product(
        self: Self,
        product_id: int,
        quantity: int,
        price: Decimal,
        name: str | None,
        image_path: str | None,
    ) -> Self:
        """Add a product to the cart."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.name = name
                item.image_path = image_path
                item.quantity += quantity
                item.price += price
                return self

        self.cart_items.append(
            ProductCart(
                product_id=product_id,
                quantity=quantity,
                price=price,
                name=name,
                image_path=image_path,
            ),
        )
        return self

    def remove_product(self: Self, product_id: int) -> Self:
        """Remove a product from the cart based on its product_id."""
        for i, item in enumerate(self.cart_items):
            if item.product_id == product_id:
                del self.cart_items[i]
                return self
        msg = f"Product id {product_id} don't exists in cart"
        logger.error(msg)
        raise IndexError(msg)

    def add_product_price(self: Self, products: list[ProductCart]) -> Self:
        """Add a product price to cart."""
        product_prices = {
            product.product_id: product.price for product in products
        }

        self.cart_items = [
            item.update_price(new_price=product_prices.get(item.product_id))
            for item in self.cart_items
        ]

    def calculate_subtotal(self: Self, discount: Decimal = 0) -> None:
        """Calculate subtotal of cart."""
        subtotal = Decimal(0)
        if not self.cart_items:
            msg = 'Cart items is empty'
            logger.error(msg)
            raise ValueError(msg)
        try:
            for item in self.cart_items:
                subtotal += item.price * item.quantity
                if discount > 0:
                    item.discount_price = item.price * discount
                    self.discount += item.discount_price * item.quantity
            self.subtotal = subtotal
            if self.freight and self.freight.price:
                self.total = subtotal + self.freight.price
        except TypeError as err:
            logger.error('Price or quantity not found in cart item')
            raise CartNotFoundPriceError from err

    def get_products_price_and_discounts(self: Self, products: list) -> None:
        """Get products price and discounts."""
        if len(self.cart_items) != len(products):
            logger.error(
                f'Cart items is diferent to product list to check. '
                f'Cart items: {self.cart_items} '
                f'Product list: {products}',
            )
            raise CartInconsistencyError
        product_dict = {product.product_id: product for product in products}
        for index, cart_item in enumerate(self.cart_items):
            product_id = cart_item.product_id
            if product_id in product_dict:
                product = product_dict[product_id]
                self.cart_items[index].price = product.price
                self.cart_items[index].name = product.name
                self.cart_items[index].image_path = product.image_path
                self.cart_items[index].discount_price = (
                    product.discount if product.discount else Decimal('0')
                )


class CartUser(CartBase):
    """Cart second step representation with logged user."""

    user_data: UserData


class CartShipping(CartUser):
    """Cart third step representation with shipping information."""

    shipping_is_payment: bool
    user_address_id: int
    shipping_address_id: int | None = None


class CartPayment(CartShipping):
    """Cart fourth step representation with payment information."""

    payment_method: str
    payment_method_id: str | None = None
    payment_intent: str | None = None
    customer_id: str | None = None
    card_token: str | None = None
    pix_qr_code: str | None = None
    pix_qr_code_base4: str | None = None
    pix_payment_id: int | None = None
    gateway_provider: str
    installments: int = 1
    subtotal_with_fee: Decimal = Decimal(0)
    total_with_fee: Decimal = Decimal(0)

    def calculate_fee(self: Self, fee: Decimal) -> None:
        """Calculate installments fee."""
        self.subtotal_with_fee = self.subtotal * (1 + fee)
        self.total_with_fee = self.subtotal_with_fee + self.freight.price


class CreateCreditCardPaymentMethod(BaseModel):
    """Create credit card payment method."""

    payment_gateway: str
    number: str
    exp_month: int
    exp_year: int
    cvc: str
    name: str
    installments: int = 1


class CreateCreditCardTokenPaymentMethod(BaseModel):
    """Create credit card token payment method."""

    payment_gateway: str
    card_token: str
    installments: int = 1


class CreatePixPaymentMethod(BaseModel):
    """Create pix payment method."""

    payment_gateway: str


class AddressCreate(BaseModel):
    """Create address model."""

    shipping_is_payment: bool
    shipping_address: ShippingAddress | None = None
    user_address: UserAddress


class CreateCheckoutResponse(BaseModel):
    """Result of create checkout."""

    status: str
    message: str


def convert_price_to_decimal(price: int) -> Decimal:
    """Convert price to decimal."""
    return Decimal(price / 100)


def generate_empty_cart() -> CartBase:
    """Generate empty cart."""
    return CartBase(
        uuid=generate_cart_uuid(),
        cart_items=[],
        subtotal=Decimal(0),
    )


def generate_new_cart(
    product: ProductInDB,
    price: Decimal,
    quantity: int,
) -> CartBase:
    """Generate new cart."""
    if not product:
        logger.error('Product not found in database')
        raise ProductNotFoundError
    _product = ProductCart(
        product_id=product.product_id,
        name=product.name,
        image_path=product.image_path,
        quantity=quantity,
        price=product.price,
        discount_price=product.discount,
    )
    return CartBase(
        uuid=generate_cart_uuid(),
        cart_items=[_product],
        subtotal=price * quantity,
    )


def validate_cache_cart(cache_cart: bytes | None):
    if not cache_cart:
        raise CartNotFoundError
    if not isinstance(cache_cart, bytes):
        raise InvalidCartFormatError
    try:
        cache_cart = json.loads(cache_cart)
    except json.JSONDecodeError:
        raise InvalidCartFormatError
