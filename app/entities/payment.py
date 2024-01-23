# ruff: noqa: ANN401 A003
import enum
from typing import Any, Self
from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class CreditCardInformation(BaseModel):
    credit_card_name: str | None = None
    credit_card_number: str | None = None
    credit_card_cvv: str | None = None
    credit_card_validate: str | None = None
    installments: int | None = None


class PaymentNotificationData(BaseModel):
    """Payment notification data."""

    id: str


class PaymentNotification(BaseModel):
    """Payment notification."""

    id: int | None
    live_mode: bool
    type: str
    user_id: str
    api_version: str
    action: str
    data: PaymentNotificationData


class PaymentStatusResponse(BaseModel):
    """Payment response."""

    payment_id: int
    gateway_payment_id: int | str
    status: str

    model_config = ConfigDict(from_attributes=True)


class AbstractPaymentGateway:
    """Abstract class to process payment."""

    def process_credit_card(self: Self) -> Any:
        """Process credit card."""
        raise NotImplementedError


class ProcessStripePayment(AbstractPaymentGateway):
    """Process payment with Stripe."""

    def process_credit_card(self: Self) -> Any:
        """Process credit card with Stripe."""


class ProcessPagarmePayment(AbstractPaymentGateway):
    """Process payment with Pagarme."""

    def process_credit_card(self: Self) -> Any:
        """Process credit card with Pagarme."""


class PaymentGateway(enum.Enum):
    STRIPE: AbstractPaymentGateway = ProcessStripePayment()
    PAGARME: AbstractPaymentGateway = ProcessPagarmePayment()


class PaymentDBUpdate(BaseModel):
    """Payment DB Update."""

    status: str
    payment_gateway: str
    authorization: str | None = None
    gateway_payment_id: int | str | None = None


class ConfigFee(BaseModel):
    """Credit card installment fee."""

    credit_card_fee_config_id: int
    min_installment_with_fee: int
    max_installments: int
    fee: Decimal
    model_config = ConfigDict(from_attributes=True)


def validate_payment(
    payment_accept: Any,
) -> str:
    """Validate payment."""
    if payment_accept.status != 'succeeded':
        msg = 'Payment not succeeded'
        raise ValueError(msg)
    return 'succeeded'
