from decimal import Decimal

from typing import Self
from pydantic import BaseModel, ConfigDict, Json
from schemas.order_schema import CategoryInDB


class ProductSoldOutError(Exception):
    """Represent produt is Sold out."""

    def __init__(self: Self) -> None:
        super().__init__('There are products in not inventory.')


INSTALLMENT_CONFIG_DEFAULT = 1


class ProductCart(BaseModel):
    """Product Representation in Cart."""

    product_id: int
    name: str | None
    image_path: str | None
    quantity: int
    available_quantity: int = 0
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


class ProductCreateResponse(BaseModel):
    name: str
    uri: str
    price: Decimal
    direct_sales: bool | None = None
    description: Json | None
    image_path: str | None = None
    installments_config: int | None = None
    installments_list: dict | None = None
    category_id: int
    discount: int | None = None
    heigth: float | None = None
    width: float | None = None
    weigth: float | None = None
    length: float | None = None
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str
    uri: str
    price: Decimal | float
    category_id: int
    description: dict | str | None
    image_path: str
    sku: str
    direct_sales: bool | None = None
    installments_config: int = INSTALLMENT_CONFIG_DEFAULT
    installments_list: dict | None = None
    discount: int | None = None
    height: int | None = None
    width: int | None = None
    weight: int | None = None
    length: int | None = None
    diameter: int | None = None
    currency: str | None = None
    model_config = ConfigDict(from_attributes=True)


class ProductInDBResponse(ProductCreate):
    product_id: int


class ListProducts(BaseModel):
    products: list[ProductInDB]
    model_config = ConfigDict(from_attributes=True)
