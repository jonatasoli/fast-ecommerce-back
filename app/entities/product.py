from decimal import Decimal

from typing import Self
from pydantic import BaseModel, ConfigDict, Json
from schemas.order_schema import CategoryInDB


class ProductSoldOutError(Exception):
    """Represent produt is Sold out."""


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
    price: Decimal
    active: bool
    direct_sales: bool
    description: Json | dict | None
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
    quantity: int = 0
    sku: str

    model_config = ConfigDict(from_attributes=True)


class ProductsResponse(BaseModel):
    """Products Response."""

    products: list[ProductInDB] | list
    page: int
    offset: int
    total_records: int
    total_pages: int


class ProductCategoryInDB(BaseModel):
    """Product Category Representation in DB."""

    product_id: int
    name: str
    uri: str
    price: Decimal
    active: bool
    direct_sales: bool
    description: Json | dict | None
    image_path: str | None
    installments_config: int | None
    installments_list: dict[str, str] | None
    discount: int | None
    category: CategoryInDB
    showcase: bool
    show_discount: bool
    height: int
    width: int
    weight: int
    length: int
    diameter: int | None
    sku: str
    quantity: int = 0

    model_config = ConfigDict(from_attributes=True)


class InventoryInDB(BaseModel):
    inventory_id: int
    product_id: int
    order_id: int | None
    quantity: int
    operation: str

    model_config = ConfigDict(from_attributes=True)


class ProductInventoryDB(ProductInDB, InventoryInDB):
    ...
