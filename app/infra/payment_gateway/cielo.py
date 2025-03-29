
from decimal import Decimal


def create_customer_in_gateway(
    user_email: str,
) -> dict:
    """Must create customer in Cielo."""
    raise NotImplementedError


def attach_customer_in_payment_method(
    payment_gateway: str,
    customer_uuid: str,
    card_token: str | None = None,
    card_issuer: str | None = None,
    card_brand: str | None = None,
    email: str | None = None,
    payment_method_id: str | None = None,
) -> str:
    """Attach a customer in payment method."""
    raise NotImplementedError


def create_credit_card_payment(
    *,
    payment_gateway: str,
    customer_id: str,
    amount: Decimal,
    card_token: str,
    installments: int,
    payment_intent_id: str,
    payment_method: str,
    customer_email: str,
) -> dict:
    """Create a credit card payment."""
    raise NotImplementedError


def accept_payment(
    payment_gateway: str,
    payment_id: str,
) -> dict:
    """Accept a payment in gateway."""
    raise NotImplementedError


def get_payment_status(
    payment_id: str | int,
    payment_gateway: str,
) -> dict:
    """Get payment status."""
    raise NotImplementedError

def cancel_payment(
    payment_id,
):
    """Cancel payment in gateway."""
    raise NotImplementedError


def create_credit_card_token():
    """Create token for credit card."""
    raise NotImplementedError


def zero_auth_credit_card():
    """Check if credit card is valid."""
    raise NotImplementedError
