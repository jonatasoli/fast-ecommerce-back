from decimal import Decimal

from typing import TypeVar
from pydantic import BaseModel

Self = TypeVar('Self')


class ProductCart(BaseModel):
    """Product Representation in Cart."""

    product_id: int
    quantity: int
    price: Decimal | None
    discount_price: Decimal = Decimal(0)

    def update_price(self: Self, new_price: Decimal) -> 'ProductCart':
        return ProductCart(
            product_id=self.product_id,
            quantity=self.quantity,
            price=new_price,
            discount_price=self.discount_price,
        )
