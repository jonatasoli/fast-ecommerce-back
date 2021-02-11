from fastapi import Header, APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from loguru import logger

from schemas.mail_schema import MailTrackingNumber
from domains import domain_mail
from endpoints import deps

mail = APIRouter()


@mail.post("/send-mail-tracking-number", status_code=201)
async def send_mail_tracking_number(
    *, db: Session = Depends(deps.get_db), mail_data: MailTrackingNumber
):
    mail = domain_mail.send_mail_tracking_number(db, mail_data=mail_data)
    if mail:
        return JSONResponse(
            content={"message": "Mail Sended"}, media_type="application/json"
        )
    return status.HTTP_417_EXPECTATION_FAILED
