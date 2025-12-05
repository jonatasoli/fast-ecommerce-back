import pytest
from unittest.mock import MagicMock
from app.entities.payment import (
    AbstractPaymentGateway,
    validate_payment,
)


def test_abstract_payment_gateway_process_credit_card_raises_not_implemented():
    """Must raise NotImplementedError for abstract method."""
    # Arrange
    gateway = AbstractPaymentGateway()

    # Act / Assert
    with pytest.raises(NotImplementedError):
        gateway.process_credit_card()


def test_validate_payment_with_succeeded_status():
    """Must return 'succeeded' when payment status is succeeded."""
    # Arrange
    payment_accept = MagicMock()
    payment_accept.status = 'succeeded'

    # Act
    result = validate_payment(payment_accept)

    # Assert
    assert result == 'succeeded'


def test_validate_payment_with_non_succeeded_status_raises_value_error():
    """Must raise ValueError when payment status is not succeeded."""
    # Arrange
    payment_accept = MagicMock()
    payment_accept.status = 'failed'

    # Act / Assert
    with pytest.raises(ValueError, match='Payment not succeeded'):
        validate_payment(payment_accept)
