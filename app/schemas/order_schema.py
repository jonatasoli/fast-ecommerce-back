from pydantic import BaseModel, SecretStr
from typing import List, Optional
from datetime import datetime


class ProductSchema(BaseModel):
    name: str
    uri: str
    price: int
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: str
    image_path: str
    installments_config: Optional[int]
    installments_list: Optional[list]


    class Config:
        orm_mode = True

class ProductResponseSchema(ProductSchema):
    id: int


class InvoiceSchema(BaseModel):
    id: int
    customer_id: int
    invoice_date: datetime
    invoice_items_id: int


class InvoiceItemsSchema(BaseModel):
    id: int
    invoice_id: int
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
    ship_name: Optional[str]
    ship_address: Optional[str]
    ship_number: Optional[str]
    ship_address_complement: Optional[str]
    ship_neighborhood: Optional[str]
    ship_city: Optional[str]
    ship_state: Optional[str]
    ship_country: Optional[str]
    ship_zip: Optional[str]
    payment_method: str
    shopping_cart: list
    credit_card_name: Optional[str]
    credit_card_number: Optional[str]
    credit_card_cvv: Optional[str]
    credit_card_validate: Optional[str]
    installments: Optional[int]


class CheckoutReceive(BaseModel):
    transaction: dict
    affiliate: Optional[str]
    cupom: Optional[str]


class CheckoutResponseSchema(BaseModel):
    token: str
    order_id: int
    name: str
    slip_payment: Optional[str]
