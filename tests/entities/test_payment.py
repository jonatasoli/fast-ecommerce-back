import pytest
from unittest.mock import MagicMock
from app.entities.payment import (
    AbstractPaymentGateway,
    validate_payment,
)


def test_abstract_payment_gateway_process_credit_card_raises_not_implemented():
    # Setup
    gateway = AbstractPaymentGateway()

    # Act / Assert
    with pytest.raises(NotImplementedError):
        gateway.process_credit_card()


def test_validate_payment_with_succeeded_status():
    # Setup
    payment_accept = MagicMock()
    payment_accept.status = 'succeeded'

    # Act
    result = validate_payment(payment_accept)

    # Assert
    assert result == 'succeeded'


def test_validate_payment_with_non_succeeded_status_raises_value_error():
    # Setup
    payment_accept = MagicMock()
    payment_accept.status = 'failed'

    # Act / Assert
    with pytest.raises(ValueError, match='Payment not succeeded'):
        validate_payment(payment_accept)
