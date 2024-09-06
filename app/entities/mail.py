from pydantic import BaseModel


class MailOrderCancelled(BaseModel):
    mail_to: str
    order_id: str | int
    reason: str


class MailOrderProcessed(BaseModel):
    mail_to: str
    order_id: int | str


class MailOrderPaied(BaseModel):
    mail_to: str
    order_id: int


class MailTrackingNumber(BaseModel):
    mail_to: str
    order_id: int
    tracking_number: str


class MailResetPassword(BaseModel):
    mail_to: str
    token: str


class MailFormCourses(BaseModel):
    name: str
    email: str
    phone: str
    course: str
    option: str


class MailInformUserProduct(BaseModel):
    product_name: str
    mail_to: str
    user_mail: str
    user_phone: str
