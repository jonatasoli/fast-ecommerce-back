import enum
from typing import Any
from pydantic import BaseModel


class CreditCardInformation(BaseModel):
    credit_card_name: str | None = None
    credit_card_number: str | None = None
    credit_card_cvv: str | None = None
    credit_card_validate: str | None = None
    installments: int | None = None


class AbsctractPaymentGateway:
    """Abstract class to process payment."""

    def process_credit_card(self):
        """Process credit card."""
        raise NotImplementedError


class ProcessStripePayment(AbsctractPaymentGateway):
    """Process payment with Stripe."""

    def process_credit_card(self):
        """Process credit card with Stripe."""


class ProcessPagarmePayment(AbsctractPaymentGateway):
    """Process payment with Pagarme."""

    def process_credit_card(self):
        """Process credit card with Pagarme."""


class PaymentGateway(enum.Enum):
    STRIPE: AbsctractPaymentGateway = ProcessStripePayment()
    PAGARME: AbsctractPaymentGateway = ProcessPagarmePayment()


def validate_payment(
    payment_accept: Any,
    gateway: AbsctractPaymentGateway,
) -> str:
    """Validate payment."""
    _ = payment_accept, gateway
    return 'succeeded'
