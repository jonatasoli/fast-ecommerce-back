from decimal import Decimal
import enum
from typing import Any
from app.entities.cart import CreateCreditCardPaymentMethod
from app.infra.constants import PaymentGatewayAvailable, PaymentMethod
from app.infra.payment_gateway import cielo, stripe_gateway, mercadopago_gateway


class PaymentGatewayCommmand(enum.Enum):
    STRIPE = stripe_gateway
    MERCADOPAGO = mercadopago_gateway
    CIELO = cielo


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
    *,
    payment_intent_id: str,
    payment_gateway: str,
    payment_method: str = '',
    customer_id: int = 0,
    customer_email: str = '',
    amount: Decimal | float = 0,
    instalments: int = 1,
) -> dict:
    """Create a credit card payment in specific gateway."""
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.create_credit_card_payment(
        payment_intent_id=payment_intent_id,
        payment_method=payment_method,
        customer_email=customer_email,
        customer_id=customer_id,
        amount=amount,
        installments=instalments,
    )


def attach_customer_in_payment_method(
    payment_gateway: str,
    customer_uuid: str,
    card_token: str | None = None,
    card_issuer: str | None = None,
    card_brand: str | None = None,
    email: str | None = None,
    payment_method_id: str | None = None,
) -> str:
    """Attach a customer in payment method in gateway."""
    _ = email
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.attach_customer_in_payment_method(
        card_token=card_token,
        card_issuer=card_issuer,
        payment_method_id=card_brand if card_brand else payment_method_id,
        customer_uuid=customer_uuid,
    )


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
    """Create a credit card payment intent in gateway."""
    gateway = PaymentGatewayCommmand[payment_gateway].value
    return gateway.create_credit_card_payment(
        payment_intent_id=payment_intent_id,
        customer_id=customer_id,
        amount=amount,
        card_token=card_token,
        installments=installments,
        payment_method=payment_method,
        customer_email=customer_email,
    )


def accept_payment(
    payment_gateway: str,
    payment_id: str,
) -> dict:
    """Accept a payment in gateway."""
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


#!TODO - Refactor payment gateway and isolate gateway functions
def create_payment_method(
    payment: CreateCreditCardPaymentMethod,
):
    """Create stripe payment method."""
    gateway = PaymentGatewayCommmand['STRIPE'].value
    return gateway.create_payment_method(
        payment=payment,
    )


def create_payment_intent(
    amount: int,
    currency: str,
    customer_id: str,
    payment_method: str,
    installments: int,
    ):
    """Create payment intent for stripe."""
    gateway = PaymentGatewayCommmand['STRIPE'].value
    return gateway.create_payment_intent(
        amount=amount,
        currency=currency,
        customer_id=customer_id,
        payment_method=payment_method,
        installments=installments,

        )


def cancel_payment(
    payment_id,
):
    """Cancel payment in gateway."""
    raise NotImplementedError
