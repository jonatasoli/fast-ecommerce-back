from pydantic import BaseModel


class OrderNotFound(Exception):
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
