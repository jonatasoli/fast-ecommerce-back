from fastapi import Depends
from sqlalchemy.orm import Session, session
from app.entities.mail import (
    MailOrderCancelled,
    MailOrderPaied,
    MailOrderProcessed,
    MailTrackingNumber,
)
from app.infra.database import get_session
from app.mail.services import (
    send_mail_tracking_number,
    send_order_cancelled,
    send_order_paid,
    send_order_processed,
)
from app.infra.worker import task_message_bus


def get_db():
    SessionLocal = get_session()
    return SessionLocal()


@task_message_bus.event('notification_order_cancelled')
def task_mail_order_cancelled(
    mail_to: str, order_id: int, reason: str, db: Session = Depends(get_db)
) -> None:
    """Send cancelled email."""
    mail_data = MailOrderCancelled(
        mail_to=mail_to, order_id=order_id, reason=reason
    )
    send_order_cancelled(db=db, mail_data=mail_data)


@task_message_bus.event('notification_order_processed')
def task_mail_order_processed(
    mail_to: str, order_id: int, db: Session = Depends(get_db)
) -> None:
    """Send cancelled email."""
    mail_data = MailOrderProcessed(
        mail_to=mail_to,
        order_id=order_id,
    )
    send_order_processed(db=db, mail_data=mail_data)


@task_message_bus.event('notification_order_paid')
def task_mail_order_paid(
    mail_to: str, order_id: int, db: Session = Depends(get_db)
) -> None:
    """Send cancelled email."""
    mail_data = MailOrderPaied(
        mail_to=mail_to,
        order_id=order_id,
    )
    send_order_paid(db=db, mail_data=mail_data)


@task_message_bus.event('notification_tracking_number')
def task_mail_order_track_number(
    mail_to: str,
    order_id: int,
    tracking_number: str,
    db: Session = Depends(get_db),
) -> None:
    """Send cancelled email."""
    mail_data = MailTrackingNumber(
        mail_to=mail_to,
        order_id=order_id,
        tracking_number=tracking_number,
    )
    send_mail_tracking_number(db=db, mail_data=mail_data)
