from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict

from app.entities.product import ProductInDB
from app.entities.user import UserInDB


class OrderNotFoundError(Exception):
    ...


class CreateOrderStatusStepError(Exception):
    ...


class OrderDBUpdate(BaseModel):
    order_id: int
    order_status: str
    customer_id: str
    tracking_number: str | None = None
    payment_id: int | None = None
    checked: bool | None = None


class OrderInDB(BaseModel):
    order_id: int
    affiliate_id: int | None
    user: UserInDB
    customer_id: str
    order_date: datetime
    discount: Decimal | None
    tracking_number: str | None
    order_status: str
    freight: str | None
    coupon_id: int | None
    model_config = ConfigDict(from_attributes=True)


class OrderItemInDB(BaseModel):
    order: OrderInDB
    products: List[ProductInDB]
    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    order_items: List[OrderItemInDB]
    page: int
    offset: int
    total_pages: int
    total_records: int


class OrderResponse(BaseModel):
    orders: List[OrderInDB]
    page: int
    offset: int
    total_pages: int
    total_records: int

