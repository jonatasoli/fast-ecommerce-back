from decimal import Decimal

from typing import Self
from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Json
from app.infra.constants import CurrencyType, InventoryOperation, MediaType


class CategoryInDB(BaseModel):
    category_id: int
    name: str
    path: str
    model_config = ConfigDict(from_attributes=True)

class ProductSoldOutError(Exception):
    """Represent produt is Sold out."""

    def __init__(self: Self) -> None:
        super().__init__('There are products in not inventory.')

class ProductNotCreatedError(Exception):
    """Represent product is not created."""

    def __init__(self: Self) -> None:
        super().__init__('Product is not created')

class ProductNotFoundError(Exception):
    """Represent product is not created."""

    def __init__(self: Self) -> None:
        super().__init__('Product not found')

INSTALLMENT_CONFIG_DEFAULT = 1


class ProductCart(BaseModel):
    """Product Representation in Cart."""

    product_id: int
    name: str | None
    image_path: str | None
    quantity: int
    available_quantity: int = 0
    price: Decimal | None = None
    description: str | None = None
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
    discount: int | Decimal | str | None
    category_id: int
    showcase: bool
    show_discount: bool
    height: int | None
    width: int | None
    weight: int | None
    length: int | None
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
    height: int | None
    width: int | None
    weight: int | None
    length: int | None
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
    sku: str
    description: dict | str | None = None
    image_path: str | None = None
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


class ProductCreateInDBResponse(ProductCreate):
    product_id: int


class ListProducts(BaseModel):
    products: list[ProductInDB]
    model_config = ConfigDict(from_attributes=True)


class InventoryTransaction(BaseModel):
    operation: InventoryOperation
    quantity: int


class InventoryResponse(BaseModel):
    inventory: list[ProductInDB]
    page: int
    offset: int
    total_pages: int
    total_records: int


class ProductPatchRequest(BaseModel):
    name: str | None = None
    sku: str | None = None
    uri: str | None = None
    active: bool | None = None
    price: float | Decimal | None = None
    direct_sales: bool | None = None
    description: Json | dict | str | None = None
    image_path: str | None = None
    installments_config: int | None = None
    installments_list: dict | None = None
    category_id: int | None = None
    discount: int | None = None
    showcase: bool | None = None
    show_discount: bool | None = None
    heigth: float | None = None
    width: float | None = None
    weigth: float | None = None
    length: float | None = None
    currency: CurrencyType | None = None
    model_config = ConfigDict(from_attributes=True)


class ProductInDBResponse(BaseModel):
    product_id: int | None = None
    name: str
    uri: str
    price: int | Decimal
    direct_sales: bool | None = None
    description: Json | None = None
    image_path: str | None = None
    installments_config: int | None = None
    installments_list: dict | None = None
    category_id: int
    discount: int | None = None
    showcase: bool
    show_discount: bool | None = None
    heigth: float | None = None
    width: float | None = None
    weigth: float | None = None
    length: float | None = None
    model_config = ConfigDict(from_attributes=True)


class UploadedMedia(BaseModel):
    type: MediaType
    order: int


class UploadedMediaCreate(UploadedMedia):
    media: UploadFile


class UploadedMediaUpdate(UploadedMedia):
    ...


class UploadedMediaInDBResponse(UploadedMedia):
    media_id: int
    uri: str
    model_config = ConfigDict(from_attributes=True)
