from dynaconf import settings
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from mail_service.sendmail import SendMail, send_mail_sendgrid

from schemas.mail_schema import MailFormCourses, MailTrackingNumber

file_loader = FileSystemLoader('email-templates')
env = Environment(loader=file_loader)


def send_mail_tracking_number(db, mail_data: MailTrackingNumber):
    template = get_mail_template_tracking(
        mail_template='mail_tracking_number',
        order_id=mail_data.order_id,
        tracking_number=mail_data.tracking_number,
        company=settings.COMPANY,
    )
    sended = send_mail(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido está a caminho!',
        plain_text_content=str(template),
        html_content=template,
        send_mail=send_mail_sendgrid,
    )
    logger.debug(template)
    if sended:
        return True
    return False


def get_mail_template_tracking(mail_template, **kwargs):
    return env.get_template('mail_tracking_number.html').render(**kwargs)


def send_mail_form_courses(db, mail_data: MailFormCourses):
    template = get_mail_template_courses(
        mail_template='mail_form_courses',
        name=mail_data.name,
        email=mail_data.email,
        phone=mail_data.phone,
        course=mail_data.course,
        option=mail_data.option,
    )
    sended = send_mail(
        from_email=settings.EMAIL_FROM,
        to_emails='relacionamento@graciellegatto.com.br',
        subject='Contato!',
        plain_text_content=str(template),
        html_content=template,
        send_mail=send_mail_sendgrid,
    )
    logger.debug(template)
    if sended:
        return True
    return False


def get_mail_template_courses(mail_template, **kwargs):
    return env.get_template('mail_form_courses.html').render(**kwargs)


def send_mail(
    from_email, to_emails, subject, plain_text_content, html_content, send_mail
):
    sended = SendMail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=plain_text_content,
        html_content=html_content,
        send_mail=send_mail,
    )
    return sended.send_mail()
