from contextlib import suppress
from mercadopago import SDK
from config import settings


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
    customer,
    token,
    issuer_id,
    payment_method_id,
    client: SDK = get_payment_client(),
):

    card_data = {
        'token': token,
        'issuer_id': issuer_id,
        'payment_method_id': payment_method_id,
    }
    card_response = client.card().create(customer['id'], card_data)
    return card_response['response']


def create_credit_card_payment(
    customer_id,
    amount,
    card_token,
    installments,
    client: SDK = get_payment_client(),
):
    payment_data = {
        'transaction_amount': amount,
        'token': card_token,
        'installments': installments,
        'payer': {'type': 'customer', 'id': customer_id},
        'capture': False,
    }

    payment_response = client.payment().create(payment_data)
    return payment_response['response']


def accept_payment(payment_id, client: SDK = get_payment_client()):
    payment_data = {'capture': True}
    payment_response = client.payment().update(payment_id, payment_data)
    return payment_response['response']


def cancel_credit_card_reservation(
    payment_id,
    client: SDK = get_payment_client(),
):
    payment_data = {'status': 'cancelled'}
    payment_response = client.payment().update(payment_id, payment_data)
    return payment_response['response']


def create_pix(customer_id, amount, client: SDK = get_payment_client()):
    payment_data = {
        'transaction_amount': amount,
        'payment_method_id': 'pix',
        'payer': {'type': 'customer', 'id': customer_id},
    }

    payment_response = client.payment().create(payment_data)
    return payment_response['response']
