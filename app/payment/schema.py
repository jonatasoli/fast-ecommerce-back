from pydantic import BaseModel, SecretStr
from typing import List, Optional
from datetime import datetime


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
    amount: int
    api_key: str
    customer: dict
    type: str
    payment_method: str
    country: str
    boleto_expiration_date: str
    email: str
    name: str
    documents: list


class ResponseGateway(BaseModel):
    user: str
    token: Optional[str]
    status: Optional[str]
    authorization_code: Optional[str]
    gateway_id: Optional[int]
    payment_method: Optional[str]
    boleto_url: Optional[str]
    boleto_barcode: Optional[str]
    errors: Optional[list]

    
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
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: str
    image_path: str
    installments_config: Optional[int]
    installments_list: Optional[list]
    category_id: int
    discount: Optional[int]
    quantity: Optional[int]
    heigth: Optional[int]
    width: Optional[int]
    weigth: Optional[int]
    length: Optional[int]

    class Config:
        orm_mode = True

class ProductResponseSchema(ProductSchema):
    id: int


class ProductInDB(BaseModel):
    id: int
    name: str
    uri: str
    price: int
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: str
    image_path: str
    installments_config: Optional[int]
    installments_list: Optional[list]
    category_id: int
    discount: Optional[int]
    quantity: Optional[int]
    showcase: bool
    show_discount: bool
    heigth: Optional[int]
    width: Optional[int]
    weigth: Optional[int]
    length: Optional[int]

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
    tracking_number: int
    payment_id: int 

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
