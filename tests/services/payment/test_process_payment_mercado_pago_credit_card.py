from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.infra.models import CreditCardFeeConfigDB
from faker import Faker

from app.entities.cart import CartPayment
from app.entities.payment import PaymentDataInvalidError, PaymentNotFoundError
from app.infra.constants import PaymentMethod
from tests.factories import (
    AddressCreateFactory,
    CartPaymentFactory,
    CartShippingFactory,
    CreateCreditCardTokenPaymentMethodFactory,
    CreatePixPaymentMethodFactory,
)
from tests.factories_db import CustomerDBFactory, UserDBFactory
from app.payment.payment_process_mercado_pago import (
    create_payment_pix,
    create_payment_credit_card,
)

fake = Faker()


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
        id='fake_payment_id',
    )
    client.create_payment_method.return_value = {'id': 'method_id'}
    client.attach_customer_in_payment_method.return_value = 'attached_method_id'
    return client


@pytest.mark.asyncio
async def test_create_payment_credit_card_success_method(mocker, mock_client, asyncdb):
    # Setup
    payment = CreateCreditCardTokenPaymentMethodFactory(payment_gateway='mercadopago')
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()
    fee = CreditCardFeeConfigDB(
        min_installment_with_fee=2,
        fee=Decimal('0.05'),
    )
    mocker.patch('app.cart.repository.get_installment_fee', return_value=fee)
    mocker.patch('app.cart.repository.update_payment_method_to_user', return_value=user)

    # Act
    cart = await create_payment_credit_card(
        payment,
        user=user,
        customer=customer,
        cache_cart=cache_cart,
        db=asyncdb,
        client=mock_client,
    )

    # Assert
    assert isinstance(cart, CartPayment)
    assert cart.payment_method == PaymentMethod.CREDIT_CARD.value
    mock_client.attach_customer_in_payment_method.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_credit_card_token_success(mocker, mock_client, asyncdb):
    # Setup
    payment = CreateCreditCardTokenPaymentMethodFactory(
        payment_gateway='mercadopago',
        card_token='token123',
        card_issuer='issuer',
        card_brand='visa',
        installments=1,
    )
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()
    fee = CreditCardFeeConfigDB(
        min_installment_with_fee=2,
        fee=Decimal('0.05'),
    )
    mocker.patch('app.cart.repository.get_installment_fee', return_value=fee)
    mocker.patch('app.cart.repository.update_payment_method_to_user', return_value=user)

    # Act
    cart = await create_payment_credit_card(
        payment,
        user=user,
        customer=customer,
        cache_cart=cache_cart,
        db=lambda: asyncdb,
        client=mock_client,
    )

    # Assert
    assert isinstance(cart, CartPayment)
    assert cart.payment_method == PaymentMethod.CREDIT_CARD.value
    mock_client.attach_customer_in_payment_method.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_credit_card_invalid_type(mocker, mock_client, asyncdb):
    # Setup
    invalid_payment = MagicMock()
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()
    fee = CreditCardFeeConfigDB(
        min_installment_with_fee=2,
        fee=Decimal('0.05'),
    )
    mocker.patch('app.cart.repository.get_installment_fee', return_value=fee)
    mocker.patch('app.cart.repository.update_payment_method_to_user', return_value=user)

    # Act
    with pytest.raises(PaymentNotFoundError):
        await create_payment_credit_card(
            invalid_payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            db=lambda: asyncdb,
            client=mock_client,
        )


@pytest.mark.asyncio
async def test_create_payment_credit_card_missing_method_id(
    mocker, mock_client, asyncdb,
):
    # Setup
    payment = CreateCreditCardTokenPaymentMethodFactory(payment_gateway='mercadopago')
    mock_client.attach_customer_in_payment_method.return_value = None
    user = UserDBFactory()
    customer = CustomerDBFactory()
    cache_cart = CartShippingFactory()
    fee = CreditCardFeeConfigDB(
        min_installment_with_fee=2,
        fee=Decimal('0.05'),
    )
    mocker.patch('app.cart.repository.get_installment_fee', return_value=fee)
    mocker.patch('app.cart.repository.update_payment_method_to_user', return_value=user)

    # Act
    with pytest.raises(PaymentNotFoundError):
        await create_payment_credit_card(
            payment,
            user=user,
            customer=customer,
            cache_cart=cache_cart,
            db=lambda: asyncdb,
            client=mock_client,
        )
