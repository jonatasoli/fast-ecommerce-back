from datetime import datetime

from pydantic import ConfigDict, BaseModel, Json, SecretStr


class ProductSchema(BaseModel):
    name: str
    uri: str
    price: int
    direct_sales: bool | None = None
    description: dict | None
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


class ProductSchemaResponse(BaseModel):
    name: str
    uri: str
    price: int
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


class ProductResponseSchema(ProductSchema):
    product_id: int


class ProductFullResponse(BaseModel):
    product_id: int | None = None
    name: str
    uri: str
    price: int
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


class ProductInDB(BaseModel):
    product_id: int
    name: str
    uri: str
    price: int
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
    sku: str
    model_config = ConfigDict(from_attributes=True)


class ListProducts(BaseModel):
    products: list[ProductInDB]
    model_config = ConfigDict(from_attributes=True)


class InstallmentSchema(BaseModel):
    cart: list


class OrderSchema(BaseModel):
    order_id: int
    customer_id: int
    order_date: datetime
    tracking_number: str
    payment_id: int
    order_status: str
    last_updated: datetime


class OrderFullResponse(BaseModel):
    order_id: int
    customer_id: int
    order_date: datetime
    tracking_number: str
    payment_id: int
    model_config = ConfigDict(from_attributes=True)


class OrderUserListResponse(BaseModel):
    order_id: int
    cancelled_at: datetime | None = None
    cancelled_reason: str | None = None
    freight: str | None = None
    order_date: datetime
    order_status: str
    tracking_number: str | None = None
    model_config = ConfigDict(from_attributes=True)


class TrackingFullResponse(BaseModel):
    tracking_number: str


class OrderCl:
    def __init__(
        self,
        payment_id: int,
        id_pagarme: str,
        status: str,
        order_id: int,
        tracking_number: str,
        order_date: str,
        user_name: str,
        email: str,
        phone: str,
        document: int,
        type_address: str,
        category: str,
        country: str,
        city: str,
        state: str,
        neighborhood: str,
        street: str,
        street_number: int,
        address_complement: str,
        zipcode: int,
        user_affiliate: str,
        amount: int,
        checked: bool,
        products: list,
    ):
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
        self.checked = checked
        self.products = products


class ProductsResponseOrder(BaseModel):
    product_name: str
    image_path: str | None = None
    price: int
    qty: int
    payment_id: int
    model_config = ConfigDict(from_attributes=True)


class OrdersPaidFullResponse(BaseModel):
    payment_id: int
    id_pagarme: int | None = None
    status: str | None = None
    order_id: int
    tracking_number: str | None = None
    order_date: str
    user_name: str
    email: str
    phone: str | None = None
    document: int
    type_address: str
    category: str
    country: str
    city: str
    state: str
    neighborhood: str
    street: str
    street_number: int
    address_complement: str | None = None
    zipcode: str
    user_affiliate: str | None = None
    amount: int
    checked: bool | None = None
    products: list
    model_config = ConfigDict(from_attributes=True)


class OrderItemsSchema(BaseModel):
    order_items_id: int
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
    ship_name: str | None = None
    ship_address: str | None = None
    ship_number: str | None = None
    ship_address_complement: str | None = None
    ship_neighborhood: str | None = None
    ship_city: str | None = None
    ship_state: str | None = None
    ship_country: str | None = None
    ship_zip: str | None = None
    payment_method: str
    shopping_cart: list
    credit_card_name: str | None = None
    credit_card_number: str | None = None
    credit_card_cvv: str | None = None
    credit_card_validate: str | None = None
    installments: int | None = None


class CheckoutReceive(BaseModel):
    transaction: dict
    affiliate: str | None = None
    cupom: str | None = None


class CheckoutResponseSchema(BaseModel):
    token: str
    order_id: int
    name: str
    slip_payment: str | None = None


class CategorySchema(BaseModel):
    category_id: int
    name: str
    path: str


class CategoryInDB(BaseModel):
    category_id: int
    name: str
    path: str
    model_config = ConfigDict(from_attributes=True)


class ImageGalleryResponse(BaseModel):
    image_gallery_id: int
    url: str
    model_config = ConfigDict(from_attributes=True)


class ListCategory(BaseModel):
    category: list[CategoryInDB]
    model_config = ConfigDict(from_attributes=True)
