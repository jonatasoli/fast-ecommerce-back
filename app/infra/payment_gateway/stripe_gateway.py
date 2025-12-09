from decimal import Decimal
from typing import Self
from loguru import logger
import stripe
from stripe import InvalidRequestError
from app.entities.cart import CreateCreditCardPaymentMethod
from app.entities.payment import PaymentAcceptError
from config import settings


def _init_stripe():
    """Initialize stripe API key if not already set."""
    if not stripe.api_key:
        stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentGatewayRequestError(Exception):
    """Payment gateway request error."""

    def __init__(self: Self) -> None:
        super().__init__('Payment status in internal analysis')


def create_customer(email: str) -> stripe.Customer:
    """Must create a customer."""
    _init_stripe()
    return stripe.Customer.create(
        email=email,
    )


def update_customer(customer_id: str, payment_method) -> stripe.Customer:
    """Must update a customer."""
    _init_stripe()
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
    _ = installments
    _init_stripe()
    if amount < 0.5:
        logger.warning(
            f'Amount inválido para PaymentIntent (amount={amount}), ajustando para 0.50 BRL',
        )
        amount = 0.5
    return stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency=currency,
        customer=customer_id,
        payment_method=payment_method,
    )


def create_credit_card_payment(
    *,
    payment_intent_id: str,
    payment_method: str,
    customer_email: str,
    card_token: str = '',
    customer_id: int,
    amount: Decimal | float = 0,
    installments: int = 1,
) -> stripe.PaymentIntent:
    """Must confirm a payment intent in Stripe case."""
    try:
        _init_stripe()
        if amount < 0.5:
            logger.warning(
                f'Valor do pagamento inválido (amount={amount}), usando mínimo de 0.50 BRL para criar PaymentIntent.',
            )
            amount = 0.5
        if not payment_intent_id:
            logger.debug(
                f'PaymentIntent ausente, criando novo. amount={amount}, customer={customer_id}, payment_method={payment_method}',
            )
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='brl',
                customer=customer_id,
                payment_method=payment_method,
                confirm=False,
            )
            payment_intent_id = intent.id
        logger.info(
            '🔄 Confirmando PaymentIntent Stripe | ID: %s | Método: %s',
            payment_intent_id,
            payment_method,
        )
        logger.debug(
            f'Confirmando PaymentIntent id={payment_intent_id} payment_method={payment_method}',
        )
        payment_accept = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method,
            receipt_email=customer_email,
            return_url=f'{settings.BASE_URL}/payment/callback',
        )
        if payment_accept.get('error'):
            logger.error(
                '❌ Erro ao confirmar PaymentIntent Stripe | Erro: %s',
                payment_accept.get('error'),
            )
            raise PaymentAcceptError(payment_accept['error'])
        logger.info(
            '✅ PaymentIntent Stripe confirmado | Status: %s | ID: %s',
            payment_accept.get('status', 'unknown'),
            payment_accept.get('id', 'unknown'),
        )
        return payment_accept
    except InvalidRequestError as error:
        logger.error('❌ Erro na requisição Stripe: %s', error)
        raise PaymentGatewayRequestError


def attach_customer_in_payment_method(
    customer_uuid: str,
    payment_method_id: str,
    card_token: str | None = None,
    card_issuer: str | None = None,
) -> str:
    """Attach a customer to a payment method and return the method id."""
    _ = card_token, card_issuer
    _init_stripe()
    try:
        logger.debug(
            f'Attaching payment_method_id={payment_method_id} to customer_uuid={customer_uuid}',
        )
        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_uuid,
        )
        logger.debug(
            f'Attach result id={getattr(payment_method, "id", None)} status={getattr(payment_method, "status", None)}',
        )
        return payment_method.id  # type: ignore[attr-defined]
    except InvalidRequestError as error:
        logger.error(f'Erro ao anexar PaymentMethod ao customer: {error}')
        if 'already been attached' in str(error).lower() or 'already attached' in str(error).lower():
            pm = stripe.PaymentMethod.retrieve(payment_method_id)
            logger.debug(
                f'PaymentMethod already attached, retrieved id={getattr(pm, "id", None)} status={getattr(pm, "status", None)}',
            )
            return pm.id  # type: ignore[attr-defined]
        raise PaymentGatewayRequestError from error


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
    _init_stripe()
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
    payment: CreateCreditCardPaymentMethod,
) -> stripe.PaymentMethod:
    """Must create a payment method."""
    _init_stripe()
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
    _init_stripe()
    return stripe.Customer.retrieve_source(
        customer,
        card_id,
    )


def accept_payment(payment_id):
    """Confirm payment."""
    return payment_id
