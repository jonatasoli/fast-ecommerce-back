import enum
from typing import Any
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod
from app.infra.payment_gateway import stripe_gateway, mercadopago_gateway


class PaymentGatewayCommmand(enum.Enum):
    STRIPE: Any = stripe_gateway
    MERCADOPAGO: Any = mercadopago_gateway


def create_customer_in_gateway(
    user_email: str,
) -> dict:
    """Create a customer in stripe and mercado pago."""
    customers = {}
    for payment_gateway in PaymentGatewayAvailable:
        gateway = PaymentGatewayCommmand[payment_gateway.value].value
        customers[payment_gateway.value] = gateway.create_customer(
            email=user_email,
        )
    return customers


def create_method_credit_card(
    payment_gateway: str,
    user_email: str,
) -> dict:
    """Create a credit card payment in stripe and mercado pago."""
    payments = {}
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.create_credit_card_payment(
        payment_method=payment_method,
        email=user_email,
    )


def attach_customer_in_payment_method(
    payment_gateway: str,
    card_token: str,
    customer_uuid: str,
    email: str,
) -> str:
    """Attach a customer in payment method in stripe and mercado pago."""
    _ = email
    gateway = PaymentGatewayCommmand[payment_gateway].value
    payment_method_id = gateway.attach_customer_in_payment_method(
        card_token=card_token,
        payment_method_id=PaymentMethod.CREDIT_CARD.value,
        customer_uuid=customer_uuid,
    )
    return payment_method_id
