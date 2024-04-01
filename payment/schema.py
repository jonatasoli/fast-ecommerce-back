from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, BaseModel, SecretStr


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
    token: str | None = None
    order_id: int
    name: str
    payment_status: str | None = None
    boleto_url: str | None = None
    boleto_barcode: str | None = None
    errors: list | None = None


class ResponseGateway(BaseModel):
    user: str
    token: str | None = None
    status: str | None = None
    authorization_code: str | None = None
    gateway_id: int | None = None
    payment_method: str | None = None
    boleto_url: str | None = None
    boleto_barcode: str | None = None
    errors: list | None = None


class ConfigCreditCardInDB(BaseModel):
    fee: str
    min_installment: int
    max_installment: int
    model_config = ConfigDict(from_attributes=True)


class ConfigCreditCardResponse(BaseModel):
    credit_card_fee_config_id: int
    fee: Decimal
    min_installment_with_fee: int
    max_installments: int
    model_config = ConfigDict(from_attributes=True)


class InstallmentSchema(BaseModel):
    cart: list


class OrderSchema(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    tracking_number: int
    payment_id: int
    order_status: str
    last_updated: datetime


class OrderFullResponse(BaseModel):
    id: int
    customer_id: int
    order_date: datetime
    tracking_number: int | None = None
    payment_id: int | None = None
    order_status: str
    last_updated: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


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
    id: int
    name: str
    path: str


class CategoryInDB(BaseModel):
    id: int
    name: str
    path: str
    menu: bool
    showcase: bool
    model_config = ConfigDict(from_attributes=True)


class ListCategory(BaseModel):
    category: list[CategoryInDB]
    model_config = ConfigDict(from_attributes=True)
