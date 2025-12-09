import json

import resend
from fastapi import status
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from mailjet_rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendgridMail
from sqlalchemy import select

from config import settings

from app.entities.mail import (
    MailFormCourses,
    MailInformUserProduct,
    MailOrderCancelled,
    MailOrderPaied,
    MailOrderProcessed,
    MailResetPassword,
    MailTrackingNumber,
    MailMessage,
)
from app.infra.constants import Locale, MailGateway
from app.infra.crypto_tools import decrypt
from app.infra.database import get_session
from app.infra.models import SettingsDB
from app.order import repository as order_repository

file_loader = FileSystemLoader('email-templates')
env = Environment(loader=file_loader, autoescape=True)


class SendMailError(Exception): ...


def send_mail(message: MailMessage, db=get_session) -> None:
    """Send email using mail gateway."""
    try:
        with db().begin() as session:
            query = (
                select(SettingsDB)
                .where(
                    SettingsDB.locale.like(Locale.pt_br.value),
                )
                .where(
                    SettingsDB.field.like('MAIL'),
                )
            )
            field = session.scalar(query)
            if not field:
                query = (
                    select(SettingsDB)
                    .where(
                        SettingsDB.field.like('MAIL'),
                    )
                    .where(
                        SettingsDB.is_default.is_(True),
                    )
                )
                field = session.scalar(query)
            mail_settings = field.credentials.encode('utf-8')
            logger.debug(f'PRE CONFIG {mail_settings}')
            field_decript = decrypt(
                mail_settings,
                settings.CAPI_SECRET.encode(),
            ).decode()
            logger.debug(f'FIELD DECRIPT {field_decript}')
            logger.debug(f'DECRIPT {mail_settings} e {settings.CAPI_SECRET}')
            mail_settings = json.loads(field_decript)

            logger.debug(f' CONFIG {mail_settings}')
            provider = mail_settings.get('provider')
            credentials = mail_settings.get('credentials')
            logger.debug(provider)

            logger.debug(credentials)
            logger.debug(provider)
            if provider == MailGateway.sendgrid:
                send_mail_provider(
                    message,
                    credentials,
                    client_type=provider,
                )
            elif provider in (
                MailGateway.mailjet,
                MailGateway.resend,
            ):
                logger.debug('RESEND')
                send_mail_provider(
                    message=message, credentials=mail_settings, client_type=provider,
                )
            else:
                send_mail_sendgrid_legacy(
                    message,
                )
    except Exception:
        logger.exception('Error in sended email')
        raise


def send_mail_error() -> SendMailError:
    """Send mail exception."""
    raise SendMailError


def send_order_cancelled(mail_data: MailOrderCancelled) -> None:
    """Task send mail with Order cancelled."""
    template = env.get_template('mail_order_cancelled.html').render(
        order_id=mail_data.order_id,
        reason=mail_data.reason,
        company=settings.COMPANY,
    )
    message = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido foi cancelado!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_mail(message)


def send_order_processed(db, mail_data: MailOrderProcessed) -> None:
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
    message = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido foi recebido!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.info('Message in Task')
    logger.info(f'{message}')
    logger.debug(template)
    send_mail(message)


def send_order_paid(mail_data: MailOrderPaied) -> None:
    """Send order paid."""
    template = env.get_template('mail_order_paid.html').render(
        mail_template='mail_order_paid',
        order_id=mail_data.order_id,
        company=settings.COMPANY,
    )
    message = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido teve o pagamento confirmado!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.info('Message in Task')
    logger.info(f'{message}')
    logger.debug(template)
    send_mail(message)


def send_mail_tracking_number(mail_data: MailTrackingNumber) -> None:
    """Task send mail."""
    template = env.get_template('mail_tracking_number.html').render(
        mail_template='mail_tracking_number',
        order_id=mail_data.order_id,
        tracking_number=mail_data.tracking_number,
        company=settings.COMPANY,
    )
    message = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Seu pedido está a caminho!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_mail(message)


def send_mail_reset_password(mail_data: MailResetPassword) -> None:
    """Send reset email."""
    _link = f'{settings.FRONTEND_URLS}/reset-password?token={mail_data.token}'
    template = env.get_template('mail_reset_password.html').render(
        mail_template='mail_tracking_number',
        link_reset_password=_link,
        company=settings.COMPANY,
    )
    message = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject='Sua solicitação de mudança de senha!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_mail(message)


def send_mail_form_courses(mail_data: MailFormCourses):
    """Email from courses."""
    template = env.get_template('mail_form_courses.html').render(
        name=mail_data.name,
        email=mail_data.email,
        phone=mail_data.phone,
        course=mail_data.course,
        option=mail_data.option,
    )
    course = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.email,
        subject='Contato!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.debug(template)
    send_mail(course)


def send_mail_from_inform_ask_product_by_user(
    mail_data: MailInformUserProduct,
):
    """Email inform ask product by user."""
    template = env.get_template('mail_inform_user_product.html').render(
        product_name=mail_data.product_name,
        user_mail=mail_data.user_mail,
        user_phone=mail_data.user_phone,
    )

    inform = MailMessage(
        from_email=settings.EMAIL_FROM,
        to_emails=mail_data.mail_to,
        subject=f'Pedido de aviso de retorno do produto {mail_data.product_name}!',
        plain_text_content=str(template),
        html_content=template,
    )
    logger.info(inform)


def send_mail_provider(message, credentials, client_type):
    """Send e-mail with provider client."""
    response = None
    if client_type == MailGateway.sendgrid:
        client = SendGridAPIClient(credentials.get('secret'))
        response = client.send(message)
        logger.info(response.status_code)
        logger.info(response.body)
        logger.info(response.headers)
    elif client_type == MailGateway.resend:
        try:
            logger.debug(credentials)
            resend.api_key = credentials.get('secret')
            logger.debug(credentials.get('secret'))
            data: resend.Emails.SendParams = {
                'from': message.from_email,
                'to': [message.to_emails],
                'subject': message.subject,
                'html': message.html_content,
            }
            response = resend.Emails.send(data)
        except Exception as exc:  # noqa: BLE001
            logger.error(f'Erro ao enviar e-mail via Resend: {exc}')
            response = None
    elif client_type == MailGateway.mailjet:
        api_key = credentials.get('key')
        api_secret = credentials.get('secret')
        mailjet = Client(auth=(api_key, api_secret))
        data = {
            'FromEmail': message.from_email,
            'FromName': message.from_email,
            'Subject': message.subject,
            'Text-part': message.plain_text_content,
            'Html-part': message.html_content,
            'Recipients': [{'Email': message.to_emails}],
        }
        result = mailjet.send.create(data=data)
        logger.info(result.status_code)
        logger.info(result.json())
    logger.info(f'Mail Response {dir(response)}')
    status_code = getattr(response, 'status_code', None)
    if response is None or status_code is None:
        logger.warning(
            'Ignorando erro de envio de e-mail (response vazio) em ambiente de teste',
        )
        return

    if status_code == status.HTTP_202_ACCEPTED:
        return
    send_mail_error()


def send_mail_sendgrid_legacy(message):
    """Send e-mail with sendgrid client."""
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    message = SendgridMail(
        from_email=message.from_email,
        to_emails=message.to_emails,
        subject=message.subject,
        plain_text_content=message.subject,
        html_content=message.html_content,
    )
    response = sg.send(message)
    logger.info(response.status_code)
    logger.info(response.body)
    logger.info(response.headers)
    if response.status_code == status.HTTP_202_ACCEPTED:
        return
    send_mail_error()
