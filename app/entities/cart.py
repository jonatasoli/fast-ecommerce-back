import enum
from decimal import Decimal
from typing import TypeVar
from uuid import UUID, uuid4

from app.entities.freight import ShippingAddress
from app.entities.payment import CreditCardInformation
from app.entities.product import ProductCart
from app.entities.user import UserAddress, UserData
from pydantic import BaseModel

Self = TypeVar('Self')


def generate_cart_uuid() -> UUID:
    """Generate UUID to Cart."""
    return uuid4()


class CartBase(BaseModel):
    """Cart first step representation."""

    uuid: UUID
    cart_items: list[ProductCart]
    discount_total: Decimal | None
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
        # self.cart_items.append(dict(product_id=product_id, quantity=quantity))
        # return self
        """Add a product to the cart."""
        for item in self.cart_items:
            if item.product_id == product_id:
                item.quantity += quantity
                return self
        
        self.cart_items.append(dict(product_id=product_id, quantity=quantity))
        return self

    def remove_product(self: Self, product_id: int) -> Self:
        """Remove a product from the cart based on its product_id."""
        for i, item in enumerate(self.cart_items):
            if item.product_id == product_id:
                del self.cart_items[i]
                return self
        raise IndexError(f"Product id {product_id} don't exists in cart")

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
