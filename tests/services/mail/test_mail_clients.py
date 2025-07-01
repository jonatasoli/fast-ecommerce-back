from faker import Faker
import pytest

from app.entities.mail import MailMessage
from app.infra.constants import MailGateway
from app.infra.crypto_tools import decrypt, encrypt
from app.mail.services import send_mail
from config import settings


fake = Faker()

def test_send_email_with_sendgrid(mocker):
    """Must raise email with sendgrid."""
    # Setup
    key = settings.CAPI_SECRET
    credential = encrypt(
        message = b'{"secret": "SENDGRID_SECRET"}',
        key=key,
    )
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    _settings = mocker.MagicMock()
    _settings.provider = MailGateway.sendgrid
    _settings.credentials = credential.decode('utf-8')
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = _settings

    fake_response = mocker.Mock()
    fake_response.status_code = 202
    fake_response.body = "OK"
    fake_response.headers = {"X-Test": "Header"}
    mock_send = mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = MailMessage(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'),
        plain_text_content=None,
        html_content=fake.text(),
    )

    # Act
    send_mail(message, db=mock_db)

    # Assert
    mock_send.assert_called_once()


def test_send_email_fallback_legacy(mocker):
    """Must raise email with legacy."""
    # Setup
    key = settings.CAPI_SECRET
    credential = encrypt(
        message = b'{"provider": "legacy"}',
        key=key,
    )
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    _settings = mocker.MagicMock()
    _settings.provider = "legacy"
    _settings.credentials = credential.decode('utf-8')
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = _settings

    fake_response = mocker.Mock()
    fake_response.status_code = 202
    fake_response.body = "OK"
    fake_response.headers = {"X-Test": "Header"}
    mock_send = mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = MailMessage(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'),
        plain_text_content=None,
        html_content=fake.text(),
    )

    # Act
    send_mail(message, db=mock_db)

    # Assert
    mock_send.assert_called_once()



def test_send_email_raises_on_failure(mocker):
    """Must raise email exception."""
    # Setup
    key = settings.CAPI_SECRET
    credential = encrypt(
        message = b'{"secret": "SENDGRID_SECRET"}',
        key=key,
    )
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    _settings = mocker.MagicMock()
    _settings.provider = MailGateway.sendgrid
    _settings.credentials = credential.decode('utf-8')
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = _settings

    fake_response = mocker.Mock()
    fake_response.status_code = 500
    fake_response.body = mocker.Mock()
    fake_response.headers = {"X-Test": "Header"}
    mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = MailMessage(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'),
        plain_text_content=None,
        html_content=fake.text(),
    )

    # Act / Assert
    with pytest.raises(Exception): # noqa: B017
        send_mail(message, db=mock_db)
