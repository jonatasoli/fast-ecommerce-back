
from decimal import Decimal


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


def create_pix(
        customer_id,
        *,
        customer_email: str,
        amount: Decimal | float,
        description: str,
        client,
):
    """Create a pix payment."""
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

def create_customer(email):
    """Create customer - in cielo is dummy function."""
    return { 'id': 'notimplemented' }
