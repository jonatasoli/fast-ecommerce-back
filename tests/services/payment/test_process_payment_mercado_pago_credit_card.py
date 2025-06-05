import pytest
from unittest.mock import AsyncMock, MagicMock
from faker import Faker

from app.entities.cart import CartPayment
from app.entities.payment import PaymentDataInvalidError, PaymentNotFoundError
from app.infra.constants import PaymentMethod
from tests.factories import AddressCreateFactory, CartPaymentFactory, CartShippingFactory, CreateCreditCardTokenPaymentMethodFactory, CreatePixPaymentMethodFactory
from tests.factories_db import CustomerDBFactory, UserDBFactory
from app.payment.payment_process_mercado_pago import create_payment_pix, create_payment_credit_card

fake = Faker()

@pytest.fixture
def mock_client(mocker):
    client = mocker.MagicMock()
    client.create_pix.return_value = MagicMock(
        point_of_interaction=MagicMock(
            transaction_data=MagicMock(
                qr_code='fake_qr',
                qr_code_base64='fake_qr_base64'
            )
        ),
        id='fake_payment_id'
    )
    client.create_payment_method.return_value = {'id': 'method_id'}
    client.attach_customer_in_payment_method.return_value = {'id': 'attached_method_id'}
    return client

@pytest.fixture
def mock_db(mocker):
    session = AsyncMock()
    session.begin.return_value.__aenter__.return_value = session
    return session

@pytest.mark.skip()
async def test_create_payment_pix_success(mock_client):
    payment = CreatePixPaymentMethodFactory(payment_gateway='mercadopago')
    user = UserDBFactory()
    cache_cart = AddressCreateFactory()
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
    assert cart.pix_payment_id == 'fake_payment_id'
    mock_client.create_pix.assert_called_once()

@pytest.mark.skip()
async def test_create_payment_pix_invalid_type(mock_client):
    invalid_payment = MagicMock()
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartPaymentFactory()

    with pytest.raises(PaymentDataInvalidError):
        await create_payment_pix(
            invalid_payment,
            payment_method=PaymentMethod.PIX.value,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            client=mock_client,
        )

@pytest.mark.skip()
async def test_create_payment_credit_card_success_method(mock_client, mock_db):
    payment = CreateCreditCardTokenPaymentMethodFactory(payment_gateway='mercadopago')
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()

    mock_repo = AsyncMock()
    mock_repo.get_installment_fee.return_value = MagicMock(
        min_installment_with_fee=2,
        fee=0.05
    )

    cart = await create_payment_credit_card(
        payment,
        user=user,
        customer=customer,
        cache_cart=cache_cart,
        db=lambda: mock_db,
        client=mock_client,
    )

    assert isinstance(cart, CartPayment)
    assert cart.payment_method == PaymentMethod.CREDIT_CARD.value
    mock_client.create_payment_method.assert_called_once()
    mock_client.attach_customer_in_payment_method.assert_called_once()

@pytest.mark.skip()
async def test_create_payment_credit_card_token_success(mock_client, mock_db):
    payment = CreateCreditCardTokenPaymentMethodFactory(
        payment_gateway='mercadopago',
        card_token='token123',
        card_issuer='issuer',
        card_brand='visa',
        installments=1,
    )
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartPaymentFactory()

    cart = await create_payment_credit_card(
        payment,
        user=user,
        customer=customer,
        cache_cart=cache_cart,
        db=lambda: mock_db,
        client=mock_client,
    )

    assert isinstance(cart, CartPayment)
    assert cart.payment_method == PaymentMethod.CREDIT_CARD.value
    mock_client.attach_customer_in_payment_method.assert_called_once()

@pytest.mark.skip()
async def test_create_payment_credit_card_invalid_type(mock_client, mock_db):
    invalid_payment = MagicMock()
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartPaymentFactory()

    with pytest.raises(PaymentNotFoundError):
        await create_payment_credit_card(
            invalid_payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            db=lambda: mock_db,
            client=mock_client,
        )

@pytest.mark.skip()
async def test_create_payment_credit_card_missing_method_id(mock_client, mock_db):
    payment = CreateCreditCardTokenPaymentMethodFactory(payment_gateway='mercadopago')
    mock_client.attach_customer_in_payment_method.return_value = {'id': None}
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartPaymentFactory()

    with pytest.raises(PaymentNotFoundError):
        await create_payment_credit_card(
            payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            db=lambda: mock_db,
            client=mock_client,
        )
