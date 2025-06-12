from faker import Faker
import pytest
from sendgrid import Mail

from app.infra.constants import MailGateway
from app.mail.services import send_mail

fake = Faker()

def test_send_email_with_sendgrid(mocker):
    """Must raise email with sendgrid."""
    # Setup
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    settings = mocker.MagicMock()
    settings.provider = MailGateway.sendgrid
    settings.credentials = {"secret": "SENDGRID_SECRET"}
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = settings

    fake_response = mocker.Mock()
    fake_response.status_code = 202
    fake_response.body = "OK"
    fake_response.headers = {"X-Test": "Header"}
    mock_send = mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = Mail(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'))

    # Act
    send_mail(message, db=mock_db)

    # Assert
    mock_send.assert_called_once()


def test_send_email_fallback_legacy(mocker):
    """Must raise email with legacy."""
    # Setup
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    settings = mocker.MagicMock()
    settings.provider = "legacy"
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = settings

    fake_response = mocker.Mock()
    fake_response.status_code = 202
    fake_response.body = "OK"
    fake_response.headers = {"X-Test": "Header"}
    mock_send = mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = Mail(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'))

    # Act
    send_mail(message, db=mock_db)

    # Assert
    mock_send.assert_called_once()



def test_send_email_raises_on_failure(mocker):
    """Must raise email exception."""
    # Setup
    mock_session = mocker.MagicMock()
    mock_db = lambda: mock_session # noqa: E731
    settings = mocker.MagicMock()
    settings.provider = MailGateway.sendgrid
    settings.credentials = {"secret": "SENDGRID_SECRET"}
    mock_session.begin.return_value.__enter__.return_value = mock_session
    mock_session.scalar.return_value = settings

    fake_response = mocker.Mock()
    fake_response.status_code = 500
    fake_response.body = mocker.Mock()
    fake_response.headers = {"X-Test": "Header"}
    mocker.patch("sendgrid.SendGridAPIClient.send", return_value=fake_response)

    message = Mail(
        from_email=fake.email(),
        to_emails=fake.email(),
        subject=fake.sentence(nb_words=6).rstrip('.'))

    # Act / Assert
    with pytest.raises(Exception): # noqa: B017
        send_mail(message, db=mock_db)
