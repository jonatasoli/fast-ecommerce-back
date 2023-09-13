from decimal import Decimal

from typing import Any, Self
from pydantic import BaseModel, ConfigDict, Json


class ProductCart(BaseModel):
    """Product Representation in Cart."""

    product_id: int
    name: str | None
    image_path: str | None
    quantity: int
    price: Decimal | None = None
    discount_price: Decimal = Decimal(0)

    def update_price(self: Self, new_price: Decimal) -> 'ProductCart':
        return ProductCart(
            product_id=self.product_id,
            quantity=self.quantity,
            name=self.name,
            image_path=self.image_path,
            price=new_price,
            discount_price=self.discount_price,
        )


class ProductInDB(BaseModel):
    """Product Representation in DB."""

    product_id: int
    name: str
    uri: str
    price: int
    active: bool
    direct_sales: bool
    description: Json | Any | None
    image_path: str | None
    installments_config: int | None
    installments_list: dict[str, str] | None
    discount: int | None
    category_id: int
    showcase: bool
    show_discount: bool
    height: int
    width: int
    weight: int
    length: int
    diameter: int | None
    sku: str

    model_config = ConfigDict(from_attributes=True)
