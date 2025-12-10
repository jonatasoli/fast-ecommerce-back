import pytest
from unittest.mock import MagicMock
from app.entities.mail import MailTrackingNumber, MailFormCourses
from tests.fake_functions import fake, fake_email, fake_url


@pytest.mark.asyncio
async def test_send_mail_tracking_number(async_client, mocker):
    # Setup
    mocker.patch('app.mail.services.send_mail_tracking_number', return_value=True)
    payload = {
        'mail_to': fake_email(),
        'order_id': fake.pyint(min_value=1, max_value=1000),
        'tracking_number': fake.pystr(),
    }

    # Act
    response = await async_client.post(
        '/notification/send-mail-tracking-number', json=payload,
    )

    assert response.status_code in [200, 201]
    assert response.json()['message'] == 'Mail Sended'


@pytest.mark.asyncio
async def test_send_mail_form_courses(async_client, mocker):
    # Setup
    mocker.patch('app.mail.services.send_mail_form_courses', return_value=True)
    payload = {
        'name': fake.name(),
        'email': fake_email(),
        'phone': fake.phone_number(),
        'course': fake.word(),
        'option': fake.word(),
    }

    # Act
    response = await async_client.post(
        '/notification/send-mail-form-courses', json=payload,
    )

    assert response.status_code in [200, 201]
    assert response.json()['message'] == 'Mail Sended'
