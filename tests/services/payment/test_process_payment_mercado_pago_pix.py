import pytest
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
import random

from app.entities.cart import CartPayment
from app.entities.payment import PaymentDataInvalidError, PaymentNotFoundError
from app.infra.constants import PaymentMethod
from tests.factories import AddressCreateFactory, CartPaymentFactory, CartShippingFactory, CreateCreditCardTokenPaymentMethodFactory, CreatePixPaymentMethodFactory
from tests.factories_db import CustomerDBFactory, UserDBFactory
from app.payment.payment_process_mercado_pago import create_payment_pix, create_payment_credit_card

fake = Faker()

pix_id = fake.random_int()

@pytest.fixture
def mock_client(mocker):
    client = mocker.MagicMock()
    client.create_pix.return_value = MagicMock(
        point_of_interaction=MagicMock(
            transaction_data=MagicMock(
                qr_code='fake_qr',
                qr_code_base64='fake_qr_base64',
            ),
        ),
        id=pix_id,
    )
    client.create_payment_method.return_value = {'id': 'method_id'}
    client.attach_customer_in_payment_method.return_value = {'id': 'attached_method_id'}
    return client

@pytest.fixture
def mock_db(mocker):
    session = AsyncMock()
    session.begin.return_value.__aenter__.return_value = session
    return session



@pytest.mark.asyncio
async def test_create_payment_pix_success(mock_client):
    payment = CreatePixPaymentMethodFactory(payment_gateway='mercadopago')
    user = UserDBFactory()
    cache_cart = CartShippingFactory()
    customer = CustomerDBFactory()

    cart = await create_payment_pix(
        payment,
        payment_method=PaymentMethod.PIX.value,
        user=user,
        customer=customer,
        cache_cart=cache_cart,
        client=mock_client,
    )

    assert isinstance(cart, CartPayment)
    assert cart.pix_qr_code == 'fake_qr'
    assert cart.pix_qr_code_base64 == 'fake_qr_base64'
    assert cart.pix_payment_id == pix_id
    mock_client.create_pix.assert_called_once()

@pytest.mark.asyncio
async def test_create_payment_pix_invalid_type(mock_client):
    invalid_payment = MagicMock()
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()

    with pytest.raises(PaymentDataInvalidError):
        await create_payment_pix(
            invalid_payment,
            payment_method=PaymentMethod.PIX.value,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            client=mock_client,
        )
