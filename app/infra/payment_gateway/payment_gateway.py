import enum
from typing import Any
from app.infra.constants import PaymentGatewayAvailable
from app.infra.payment_gateway import stripe_gateway, mercadopago_gateway
from pydantic import BaseModel


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
