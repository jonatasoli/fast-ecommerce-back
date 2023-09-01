from pydantic import BaseModel


class OrderNotFound(Exception):
    ...


class CreateOrderStatusStepError(Exception):
    ...


class OrderDBUpdate(BaseModel):
    order_id: int
    status: str
    customer_id: str
    tracking_number: str | None
    payment_id: int | None
    order_status: str
    checked: bool | None
