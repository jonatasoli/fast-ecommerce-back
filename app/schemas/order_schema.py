from pydantic import BaseModel, SecretStr
from typing import List, Optional, Dict
from datetime import datetime, date


class ProductSchema(BaseModel):
    name: str
    uri: str
    price: int
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: str
    image_path: Optional[str]
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


class ProductFullResponse(BaseModel):
    id: Optional[int]
    name: str
    uri: str
    price: int
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: Optional[str]
    image_path: Optional[str]
    installments_config: Optional[int]
    installments_list: Optional[list]
    category_id: int
    discount: Optional[int]
    quantity: Optional[int]
    showcase: bool
    show_discount: Optional[bool]
    heigth: Optional[int]
    width: Optional[int]
    weigth: Optional[int]
    length: Optional[int]

    class Config:
        orm_mode = True


class ProductInDB(BaseModel):
    id: int
    name: str
    uri: str
    price: int
    direct_sales: Optional[bool] = None
    upsell: Optional[list] = None
    description: Optional[str]
    image_path: Optional[str]
    installments_config: Optional[int]
    installments_list: Optional[list]
    category_id: int
    discount: Optional[int]
    quantity: Optional[int]
    showcase: bool
    show_discount: Optional[bool]
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
    tracking_number: str
    payment_id: int
    order_status: str
    last_updated: datetime


class OrderFullResponse(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    tracking_number: str
    payment_id: int

    class Config:
        orm_mode = True

class TrackingFullResponse(BaseModel):
    tracking_number: str

class OrderCl:
    def __init__(self, payment_id: int,id_pagarme: str, status: str ,
    order_id: int, tracking_number: str, order_date: str, user_name: str, 
    email: str, phone: str,  document: int, type_address: str, category: str, 
    country: str, city: str, state: str,  neighborhood: str, 
    street: str, street_number: int, address_complement: str, 
    zipcode: int, user_affiliate: str,
    amount: int, products: list):
        self.payment_id = payment_id
        self.id_pagarme = id_pagarme
        self.status = status
        self.order_id = order_id
        self.tracking_number = tracking_number
        self.order_date = order_date
        self.user_name = user_name
        self.email = email
        self.phone = phone
        self.document = document
        self.type_address = type_address
        self.category = category 
        self.country = country 
        self.city = city
        self.state = state 
        self.neighborhood = neighborhood 
        self.street = street 
        self.street_number = street_number 
        self.address_complement = address_complement 
        self.zipcode = zipcode 
        self.user_affiliate = user_affiliate 
        self.amount = amount 
        self.products = products

class ProductsResponseOrder(BaseModel):
    product_name: str
    image_path: str
    price: int
    qty: int
    payment_id: int

    class Config:
        orm_mode= True       

class OrdersPaidFullResponse(BaseModel):
    payment_id: int
    id_pagarme: Optional[int]
    status: Optional[str]
    order_id: int
    tracking_number: Optional[str]
    order_date: str
    user_name: str
    email: str
    phone: Optional[str]
    document: int
    type_address: str
    category: str
    country: str
    city: str
    state: str
    neighborhood: str
    street: str
    street_number: int
    address_complement: Optional[str]
    zipcode: str
    user_affiliate: Optional[str]
    amount: int
    products: list

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


class ImageGalleryResponse(BaseModel):
    id: int
    url: str

    class Config:
        orm_mode = True


class ListCategory(BaseModel):
    category: List[CategoryInDB]

    class Config:
        orm_mode = True
