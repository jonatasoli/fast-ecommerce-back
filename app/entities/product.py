from decimal import Decimal

from pydantic import BaseModel


class ProductCart(BaseModel):
    """Product Representation in Cart."""

    product_id: int
    quantity: int
    price: Decimal | None
    discount_price: Decimal | None
