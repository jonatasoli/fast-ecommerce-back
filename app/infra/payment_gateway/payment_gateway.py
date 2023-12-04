from decimal import Decimal
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
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.create_credit_card_payment(
        payment_method=payment_method,
        email=user_email,
    )


def attach_customer_in_payment_method(
    payment_gateway: str,
    card_token: str,
    card_issuer: str,
    card_brand: str,
    customer_uuid: str,
    email: str,
) -> str:
    """Attach a customer in payment method in stripe and mercado pago."""
    _ = email
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.attach_customer_in_payment_method(
        card_token=card_token,
        card_issuer=card_issuer,
        payment_method_id=card_brand,
        customer_uuid=customer_uuid,
    )


def create_credit_card_payment(
    payment_gateway: str,
    customer_id: str,
    amount: Decimal,
    card_token: str,
    installments: int,
) -> dict:
    """Create a credit card payment in stripe and mercado pago."""
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.create_credit_card_payment(
        customer_id=customer_id,
        amount=amount,
        card_token=card_token,
        installments=installments,
    )


def accept_payment(
    payment_gateway: str,
    payment_id: str,
) -> dict:
    """Accept a payment in stripe and mercado pago."""
    gateway = PaymentGatewayCommmand[payment_gateway].value
    payment = gateway.accept_payment(
        payment_id=payment_id,
    )
    if not payment:
        msg = 'Payment not found'
        raise Exception(msg)
    return payment


def get_payment_status(
    payment_id: str | int,
    payment_gateway: str,
) -> dict:
    """Get payment status in gateway."""
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.get_payment_status(
        payment_id=payment_id,
    )
