from schemas.mail_schema import MailTrackingNumber
from jinja2 import Template
from fastapi.responses import HTMLResponse
from dynaconf import settings
from mail_service.sendmail import SendMail, send_mail_sendgrid
from loguru import logger


def send_mail_tracking_number(db, mail_data: MailTrackingNumber):
    template = get_mail_template(
            mail_template='mail_tracking_number',
            order_id=mail_data.order_id,
            tracking_number=mail_data.tracking_number,
            company=settings.COMPANY)
    sended =send_mail(
            from_email=mail_data.mail_from,
            to_emails=mail_data.mail_to,
            subject="Seu pedido está a caminho!",
            plain_text_content=str(template),
            html_content=template,
            send_mail=send_mail_sendgrid
            )

    if sended:
        return True
    return False


def get_mail_template(mail_template, **kwargs):
    return Template(
            f"email-templates/build/{mail_template}.html").render(**kwargs)


def send_mail(from_email, to_emails, subject, plain_text_content, html_content,
        send_mail):
    sended = SendMail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            plain_text_content=plain_text_content,
            html_content=html_content,
            send_mail=send_mail
            )
    return sended.send_mail()
