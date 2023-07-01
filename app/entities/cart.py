import enum
from decimal import Decimal
from typing import TypeVar
from uuid import UUID, uuid4

from app.entities.freight import ShippingAddress
from app.entities.payment import CreditCardInformation
from app.entities.product import ProductCart
from app.entities.user import UserAddress, UserData
from app.entities.coupon import CouponBase
from pydantic import BaseModel

Self = TypeVar('Self')


class CartNotFoundPriceError(Exception):
    """Raise when cart not found price."""

    def __init__(self: Self) -> None:
        super().__init__('Price or quantity not found in cart item')


def generate_cart_uuid() -> UUID:
    """Generate UUID to Cart."""
    return uuid4()


class CartBase(BaseModel):
    """Cart first step representation."""

    uuid: UUID
    cart_items: list[ProductCart]
    coupon: CouponBase | None
    discount: Decimal = Decimal(0)
    subtotal: Decimal

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

    def add_product(self: Self, product_id: int, quantity: int) -> Self:
        """Add a product to the cart."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.quantity += quantity
                return self

        self.cart_items.append(
            {'product_id': product_id, 'quantity': quantity},
        )
        return self

    def remove_product(self: Self, product_id: int) -> Self:
        """Remove a product from the cart based on its product_id."""
        for i, item in enumerate(self.cart_items):
            if item.product_id == product_id:
                del self.cart_items[i]
                return self
        msg = f"Product id {product_id} don't exists in cart"
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
            raise ValueError(msg)
        try:
            for item in self.cart_items:
                subtotal += item.price * item.quantity
                if discount > 0:
                    item.discount_price = item.price * discount
                    self.discount += item.discount_price * item.quantity
            self.subtotal = subtotal
        except TypeError as err:
            raise CartNotFoundPriceError from err


class CartUser(CartBase):
    """Cart second step representation with logged user."""

    user_data: UserData


class CartShipping(CartUser):
    """Cart third step representation with shipping information."""

    shipping_is_payment: bool
    shipping_address: ShippingAddress | None
    user_address: UserAddress


class CartPayment(CartShipping):
    """Cart fourth step representation with payment information."""

    payment_method: enum.Enum
    credit_card_information: CreditCardInformation
