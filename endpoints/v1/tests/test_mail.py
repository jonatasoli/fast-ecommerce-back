from unittest import mock

import pytest

from schemas.mail_schema import MailTrackingNumber

mail = {
    'from': {'email': 'from@email.com'},
    'subject': 'Seu pedido está a caminho!',
    'personalizations': [{'to': [{'email': 'to@mail.com'}]}],
    'content': [
        {
            'type': 'text/plain',
            'value': 'email-templates/build/mail_tracking_number.html',
        },
        {
            'type': 'text/html',
            'value': 'email-templates/build/mail_tracking_number.html',
        },
    ],
}


@pytest.mark.skip()
@mock.patch('domains.domain_mail.send_mail', return_value=mail)
def test_send_mail(t_client):
    mail_data = MailTrackingNumber(
        mail_from='from@email.com',
        mail_to='to@email.com',
        order_id=1,
        tracking_number='BR000000001BR',
    )
    from loguru import logger

    resp = t_client.post('/send-mail-tracking-number', data=mail_data.json())

    assert resp.status_code == 200
    logger.debug(f'JSON --- {resp.json()}')
    assert resp.json().get('message') == 'Mail Sended'
