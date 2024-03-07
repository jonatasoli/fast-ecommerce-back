from fastapi import status
from sqlalchemy.orm import Session
from config import settings
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.order import repository as order_repository

from app.entities.mail import (
    MailFormCourses,
    MailOrderCancelled,
    MailOrderPaied,
    MailOrderProcessed,
    MailResetPassword,
    MailTrackingNumber,
)

file_loader = FileSystemLoader('email-templates')
env = Environment(loader=file_loader)


class SendMailError(Exception):
    ...


def send_email(message: Mail) -> None:
    """Send email using Sendgrid."""
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(response.status_code)
        logger.info(response.body)
        logger.info(response.headers)
        if response.status_code == status.HTTP_202_ACCEPTED:
            return
        send_mail_error()
    except Exception:
        logger.exception('Error in sended email')
        raise


def send_mail_error() -> SendMailError:
    """Send mail exception."""
    raise SendMailError


def send_order_cancelled(db, mail_data: MailOrderCancelled) -> None:
    """Task send mail with Order cancelled."""
    template = env.get_template('mail_order_cancelled.html').render(
        order_id=mail_data.order_id,
        reason=mail_data.reason,
        company=settings.COMPANY,
    )
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido foi cancelado!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_email(message)


def send_order_processed(db: Session, mail_data: MailOrderProcessed) -> None:
    """Task to send mail order processed."""
    order_items = None
    template = None
    with db.begin() as session:
        order_items = order_repository.get_order_items(
            order_id=mail_data.order_id,
            transaction=session,
        )
        template = env.get_template('mail_order_processed.html').render(
            mail_template='mail_order_processed',
            order_id=mail_data.order_id,
            order_items=order_items,
            company=settings.COMPANY,
        )
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido foi recebido!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.info('Message in Task')
    logger.info(f'{message}')
    logger.debug(template)
    send_email(message)


def send_order_paid(db, mail_data: MailOrderPaied) -> None:
    """Send order paid."""
    template = env.get_template('mail_order_paid.html').render(
        mail_template='mail_order_paid',
        order_id=mail_data.order_id,
        company=settings.COMPANY,
    )
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido teve o pagamento confirmado!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.info('Message in Task')
    logger.info(f'{message}')
    logger.debug(template)
    send_email(message)


def send_mail_tracking_number(db, mail_data: MailTrackingNumber) -> None:
    """Task send mail."""
    template = env.get_template('mail_tracking_number.html').render(
        mail_template='mail_tracking_number',
        order_id=mail_data.order_id,
        tracking_number=mail_data.tracking_number,
        company=settings.COMPANY,
    )
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido está a caminho!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_email(message)


def send_mail_reset_password(db, mail_data: MailResetPassword) -> None:
    """Send reset email."""
    _link = f'{settings.FRONTEND_URLS}/{mail_data.token}'
    template = env.get_template('mail_reset_password.html').render(
        mail_template='mail_tracking_number',
        link_reset_password=_link,
        company=settings.COMPANY,
    )
    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Sua solicitação de mudança de senha!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_email(message)


def send_mail_form_courses(db, mail_data: MailFormCourses):
    """Email from courses."""
    template = env.get_template('mail_form_courses.html').render(
        name=mail_data.name,
        email=mail_data.email,
        phone=mail_data.phone,
        course=mail_data.course,
        option=mail_data.option,
    )
    course = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.email,
        subject='Contato!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_email(course)
