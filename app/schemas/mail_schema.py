from typing import List
from pydantic import BaseModel


class MailTrackingNumber(BaseModel):
    mail_to: str
    order_id: int
    tracking_number: str
