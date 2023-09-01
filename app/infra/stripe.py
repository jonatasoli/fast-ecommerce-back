from typing import Self
from loguru import logger
import stripe
from stripe.error import InvalidRequestError
from app.entities.cart import CreatePaymentMethod
from config import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentGatewayRequestError(Exception):
    """Payment gateway request error."""

    def __init__(self: Self) -> None:
        super().__init__('Payment status in internal analysis')

    ...


def create_customer(email: str) -> stripe.Customer:
    """Must create a customer."""
    return stripe.Customer.create(
        email=email,
    )


def update_customer(customer_id: str, payment_method) -> stripe.Customer:
    """Must update a customer."""
    return stripe.Customer.modify(
        customer_id,
        invoice_settings={
            'default_payment_method': payment_method,
        },
    )


def create_payment_intent(
    amount: int,
    currency: str,
    customer_id: str,
    payment_method: str,
    installments: int,
) -> stripe.PaymentIntent:
    """Must create a payment intent."""
    return stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        customer=customer_id,
        payment_method=payment_method,
        payment_method_options={
            'card': {
                'installments': installments,
            },
        },
    )


def confirm_payment_intent(
    payment_intent_id: str,
    payment_method: str,
    receipt_email: str,
) -> stripe.PaymentIntent:
    """Must confirm a payment intent."""
    try:
        return stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method,
            receipt_email=receipt_email,
        )
    except InvalidRequestError as error:
        logger.error(error)
        raise PaymentGatewayRequestError


def attach_customer_in_payment_method(
    payment_method_id: str,
    customer_id: str,
) -> stripe.PaymentMethod:
    """Must attach a customer in payment method."""
    return stripe.PaymentMethod.attach(
        payment_method_id,
        customer=customer_id,
    )


def create_credit_card(  # noqa: PLR0913
    number: str,
    exp_month: int,
    exp_year: int,
    cvc: str,
    name: str,
    address: dict,
    customer: str,
) -> stripe.PaymentMethod:
    """Must create a credit card."""
    return stripe.Customer.create_source(
        customer,
        source={
            'object': 'card',
            'number': number,
            'exp_month': exp_month,
            'exp_year': exp_year,
            'cvc': cvc,
            'name': name,
            'address': address,
        },
    )


def create_payment_method(
    payment: CreatePaymentMethod,
) -> stripe.PaymentMethod:
    """Must create a payment method."""
    return stripe.PaymentMethod.create(
        type='card',
        card={
            'number': payment.number,
            'exp_month': payment.exp_month,
            'exp_year': payment.exp_year,
            'cvc': payment.cvc,
        },
    )


def retrieve_card(
    customer: str,
    card_id: str,
) -> stripe.PaymentMethod:
    """Must retrieve a card."""
    return stripe.Customer.retrieve_source(
        customer,
        card_id,
    )
