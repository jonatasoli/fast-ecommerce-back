from contextlib import suppress
from decimal import Decimal
from mercadopago import SDK
from pydantic import BaseModel
from config import settings


class CardAlreadyUseError(Exception):
    """Raise when card already use."""


class TransactionPixData(BaseModel):
    """Pix qr codes"""

    qr_code: str
    qr_code_base64: str


class PointOfInteraction(BaseModel):
    """Point Of interaction model"""

    transaction_data: TransactionPixData


class MercadoPagoPaymentResponse(BaseModel):
    """Mercado Pago payment response."""

    id: int
    authorization_code: str
    date_created: str
    date_approved: str | None = None
    currency_id: str
    payment_method: dict
    status: str
    status_detail: str | None
    currency_id: str
    transaction_amount: Decimal
    payer: dict
    card: dict | None = None
    amounts: dict | None = None


class MercadoPagoPixPaymentResponse(BaseModel):
    """Mercado Pago payment response."""

    id: int
    date_created: str
    date_approved: str | None = None
    payment_method: dict
    status: str
    status_detail: str | None
    currency_id: str
    currency_id: str
    transaction_amount: Decimal
    payer: dict
    point_of_interaction: PointOfInteraction
    amounts: dict | None = None


def get_payment_client():
    return SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)


def create_customer(email, client: SDK = get_payment_client()):
    customer_data = {'email': email}
    filters = {'email': email}

    customers_response = client.customer().search(filters=filters)
    get_customer = customers_response['response']
    customer = None
    with suppress(IndexError):
        customer = get_customer.get('results')[0]
    if not customer:
        customer_response = client.customer().create(customer_data)
        customer = customer_response['response']
    return customer


def attach_customer_in_payment_method(
    customer_uuid: str,
    payment_method_id: str,
    card_token: str,
    client: SDK = get_payment_client(),
):
    """Attach a customer in payment method in stripe and mercado pago."""
    _ = payment_method_id

    card_data = {
        'token': card_token,
    }
    card_response = None
    card_response = client.card().create(customer_uuid, card_data)
    if card_response.get('error'):
        raise CardAlreadyUseError(card_response.get('message'))
    if card_response['status'] != 201:
        raise Exception(card_response)

    return card_response['response']['id']


def create_credit_card_payment(
    customer_id,
    amount,
    card_token,
    installments,
    client: SDK = get_payment_client(),
):
    payment_data = {
        'transaction_amount': float(amount),
        'token': card_token,
        'installments': installments,
        'payer': {'type': 'customer', 'id': customer_id},
        'capture': False,
    }
    payment_response = client.payment().create(payment_data)
    if payment_response.get('error'):
        raise Exception(payment_response)
    if payment_response['status'] == 400:
        raise CardAlreadyUseError(payment_response.get('message'))
    return MercadoPagoPaymentResponse.model_validate(
        payment_response['response'],
    )


def accept_payment(payment_id, client: SDK = get_payment_client()):
    payment_data = {'capture': True}
    payment_response = client.payment().update(payment_id, payment_data)
    return MercadoPagoPaymentResponse.model_validate(
        payment_response['response'],
    )


def cancel_credit_card_reservation(
    payment_id,
    client: SDK = get_payment_client(),
):
    payment_data = {'status': 'cancelled'}
    payment_response = client.payment().update(payment_id, payment_data)
    return MercadoPagoPaymentResponse.model_validate(
        payment_response['response'],
    )


def create_pix(customer_id, amount, client: SDK = get_payment_client()):
    payment_data = {
        'transaction_amount': amount,
        'payment_method_id': 'pix',
        'payer': {'type': 'customer', 'id': customer_id},
    }

    payment_response = client.payment().create(payment_data)
    _payment = MercadoPagoPixPaymentResponse.model_validate(
        payment_response['response'],
    )
    return _payment
