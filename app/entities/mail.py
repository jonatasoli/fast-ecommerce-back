from pydantic import BaseModel


class MailOrderCancelled(BaseModel):
    mail_to: str
    order_id: int
    reason: str


class MailOrderProcessed(BaseModel):
    mail_to: str
    order_id: int


class MailOrderPaied(BaseModel):
    mail_to: str
    order_id: int


class MailTrackingNumber(BaseModel):
    mail_to: str
    order_id: int
    tracking_number: str


class MailFormCourses(BaseModel):
    name: str
    email: str
    phone: str
    course: str
    option: str
