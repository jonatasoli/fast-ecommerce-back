from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, SecretStr


class CreditCardPayment(BaseModel):
    api_key: str
    amount: int
    card_number: str
    card_cvv: str
    card_expiration_date: str
    card_holder_name: str
    installments: str
    customer: dict
    billing: dict
    shipping: dict
    items: list


class SlipPayment(BaseModel):
    amount: str
    api_key: str
    customer: dict
    type: str
    payment_method: str
    country: str
    boleto_expiration_date: str
    email: str
    name: str
    documents: list


class PaymentResponse(BaseModel):
    token: str | None
    order_id: int
    name: str
    payment_status: str | None
    boleto_url: str | None
    boleto_barcode: str | None
    errors: list | None


class ResponseGateway(BaseModel):
    user: str
    token: str | None
    status: str | None
    authorization_code: str | None
    gateway_id: int | None
    payment_method: str | None
    boleto_url: str | None
    boleto_barcode: str | None
    errors: list | None


class ConfigCreditCardInDB(BaseModel):
    fee: str
    min_installment: int
    max_installment: int

    class Config:
        orm_mode = True


class ConfigCreditCardResponse(BaseModel):
    id: int
    fee: str
    min_installment_with_fee: int
    mx_installments: int

    class Config:
        orm_mode = True


class ProductSchema(BaseModel):
    name: str
    uri: str
    price: int
    direct_sales: bool | None = None
    upsell: list | None = None
    description: str
    image_path: str
    installments_config: int | None
    installments_list: list | None
    category_id: int
    discount: int | None
    quantity: int | None
    height: int | None
    width: int | None
    weight: int | None
    length: int | None
    diameter: int | None

    class Config:
        orm_mode = True


class ProductResponseSchema(ProductSchema):
    id: int


class ProductInDB(BaseModel):
    id: int
    name: str
    uri: str
    price: int
    direct_sales: bool | None = None
    upsell: list | None = None
    description: str
    image_path: str
    installments_config: int | None
    installments_list: list | None
    category_id: int
    discount: int | None
    quantity: int | None
    showcase: bool
    show_discount: bool
    heigth: int | None
    width: int | None
    weigth: int | None
    length: int | None

    class Config:
        orm_mode = True


class ListProducts(BaseModel):
    products: List[ProductInDB]

    class Config:
        orm_mode = True


class InstallmentSchema(BaseModel):
    cart: list


class OrderSchema(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    # order_items_id: int
    tracking_number: int
    payment_id: int
    order_status: str
    last_updated: datetime


class OrderFullResponse(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    tracking_number: int | None
    payment_id: int | None
    order_status: str
    last_updated: Optional[datetime]

    class Config:
        orm_mode = True


class OrderItemsSchema(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int


class CheckoutSchema(BaseModel):
    mail: str
    document: str
    phone: str
    password: SecretStr
    name: str
    address: str
    address_number: str
    address_complement: str
    neighborhood: str
    city: str
    state: str
    country: str
    zip_code: str
    shipping_is_payment: bool
    ship_name: str | None
    ship_address: str | None
    ship_number: str | None
    ship_address_complement: str | None
    ship_neighborhood: str | None
    ship_city: str | None
    ship_state: str | None
    ship_country: str | None
    ship_zip: str | None
    payment_method: str
    shopping_cart: list
    credit_card_name: str | None
    credit_card_number: str | None
    credit_card_cvv: str | None
    credit_card_validate: str | None
    installments: int | None


class CheckoutReceive(BaseModel):
    transaction: dict
    affiliate: str | None
    cupom: str | None


class CheckoutResponseSchema(BaseModel):
    token: str
    order_id: int
    name: str
    slip_payment: str | None


class CategorySchema(BaseModel):
    id: int
    name: str
    path: str


class CategoryInDB(BaseModel):
    id: int
    name: str
    path: str

    class Config:
        orm_mode = True


class ListCategory(BaseModel):
    category: List[CategoryInDB]

    class Config:
        orm_mode = True
