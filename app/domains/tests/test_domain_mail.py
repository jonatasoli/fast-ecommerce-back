from domains import domain_mail
from domains.domain_mail import (
    send_mail_tracking_number,
    send_mail,
    get_mail_template,
)
from schemas.mail_schema import MailTrackingNumber

# Verificador de e-mail
## Verifica qual o tipo de email ele vai enviar e vai passar o from / to / args

# Envio de pagamento foi criado
# Receber o from / to / token de pagamento/ id do pedido
# Pegar o arquivo de template
# passar os dados do from / to / mail pro send_mail
# Não tem retorno

# Envio de pagamento realizado


def test_read_template_file():
    """Must read template file"""
    ...


# passar os dados do from / to / mail pro send_mail
def test_send_to_mail_gateway(mocker, monkeypatch):
    """Must receive data and process to sendgrid"""
    mail_schema = MailTrackingNumber(
        mail_from="from@mail.com",
        mail_to="to@mail.com",
        order_id=1,
        tracking_number="BR00001L2",
    )
    mail_template = "<html><body><h1>Mail</h1></body></html>"
    mocker.patch(
        "domains.domain_mail.get_mail_template", return_value=mail_template
    )
    # monkeypatch.setattr(domain_mail, 'open_mail_template', mail_template)
    # monkeypatch.setattr(domain_mail, 'send_mail', True)

    # send_mail_tracking_number(mail_data=mail_schema)
    # send_mail_tracking_number.assert_called_once_with('tracking_number_mail')
    # send_mail_tracking_number.assert_called_once_with(
    #         "from@mail.com",
    #         "to@mail.com",
    #         "Seu pedido foi enviado",
    #         "Mail",
    #         mail_template
    #         )


# Envio de código de rastreio
# Receber o from / to / código de rastreio / id do pedido
# Pegar o arquivo de template
# passar os dados do from / to / mail pro send_mail
# Não tem retorno
