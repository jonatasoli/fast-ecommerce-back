from config import settings
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.entities.mail import (
    MailFormCourses,
    MailOrderCancelled,
    MailOrderPaied,
    MailOrderProcessed,
    MailTrackingNumber,
)

file_loader = FileSystemLoader('email-templates')
env = Environment(loader=file_loader)


def send_email(message: Mail) -> bool:
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(response.status_code)
        logger.info(response.body)
        logger.info(response.headers)
        if response.status_code == 202:
            return True
        return False
    except Exception as e:
        logger.info(e.message)


def send_order_cancelled(db, mail_data: MailOrderCancelled):
    template = get_mail_template_cancelled(
        mail_template='mail_order_cancelled',
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
    sended = send_email(message)
    if sended:
        logger.info('Sended email')
        return True
    logger.info('Not sended email')
    return False


def get_mail_template_cancelled(mail_template, **kwargs):
    return env.get_template('mail_order_cancelled.html').render(**kwargs)


def send_order_processed(db, mail_data: MailOrderProcessed):
    template = get_mail_template_order_processed(
        mail_template='mail_order_processed',
        order_id=mail_data.order_id,
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
    sended = send_email(message)
    if sended:
        logger.info('Sended email')
        return True
    logger.info('Not sended email')
    return False


def get_mail_template_order_processed(mail_template, **kwargs):
    return env.get_template('mail_order_processed.html').render(**kwargs)


def send_order_paid(db, mail_data: MailOrderPaied):
    template = get_mail_template_order_paid(
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
    sended = send_email(message)
    if sended:
        logger.info('Sended email')
        return True
    logger.info('Not sended email')
    return False


def get_mail_template_order_paid(mail_template, **kwargs):
    return env.get_template('mail_order_paid.html').render(**kwargs)


def send_mail_tracking_number(db, mail_data: MailTrackingNumber):
    template = get_mail_template_tracking(
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
    sended = send_email(message)
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
    sended = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails='relacionamento@graciellegatto.com.br',
        subject='Contato!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    sended = send_email(message)
    if sended:
        return True
    return False


def get_mail_template_courses(mail_template, **kwargs):
    return env.get_template('mail_form_courses.html').render(**kwargs)
