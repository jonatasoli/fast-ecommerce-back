# ruff: noqa: I001
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.entities.payment import (
    PaymentInDB,
    PaymentStatusResponse,
    ConfigCreditCardResponse,
)
from tests.fake_functions import fake, fake_decimal


@pytest.mark.asyncio
async def test_create_config(async_client, mocker):
    # Setup
    config_id = fake.pyint(min_value=1, max_value=1000)
    max_installments = fake.pyint(min_value=1, max_value=12)
    min_installment_with_fee = fake.pyint(min_value=1, max_value=5)
    fee = fake_decimal(min_value=0, max_value=10, right_digits=2)

    mock_response = ConfigCreditCardResponse(
        config_credit_card_response_id=config_id,
        max_installments=max_installments,
        min_installment_with_fee=min_installment_with_fee,
        fee=str(fee),
    )
    mock_config = MagicMock()
    mock_config.create_installment_config.return_value = mock_response
    mocker.patch('app.payment.repository.CreditCardConfig', return_value=mock_config)

    payload = {
        'fee': str(fee),
        'min_installment': min_installment_with_fee,
        'max_installment': max_installments,
    }

    # Act
    response = await async_client.post('/payment/create-config', json=payload)

    # Assert
    assert response.status_code == 201
    assert response.json()['max_installments'] == max_installments


@pytest.mark.asyncio
async def test_payment_callback(async_client, mocker):
    # Setup
    mocker.patch('app.payment.services.update_payment', return_value=None)
    mocker.patch('app.infra.endpoints.payment.bootstrap', new_callable=AsyncMock)

    # Act
    response = await async_client.post('/payment/callback', json={'status': 'approved'})

    # Assert
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_payment_status_post(async_client, mocker):
    # Setup
    payment_id = fake.pyint(min_value=1, max_value=1000)
    gateway_payment_id = fake.pystr()
    mock_status = PaymentStatusResponse(
        status='approved',
        payment_id=payment_id,
        gateway_payment_id=gateway_payment_id,
    )
    mocker.patch('app.payment.services.get_payment_status', return_value=mock_status)
    mocker.patch('app.infra.endpoints.payment.bootstrap', new_callable=AsyncMock)

    # Act
    response = await async_client.post(
        f'/payment/payment_status?gateway_payment_id={gateway_payment_id}',
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['status'] == 'approved'


@pytest.mark.asyncio
async def test_get_payment(async_client, mocker):
    # Setup
    payment_id = fake.pyint(min_value=1, max_value=1000)
    order_id = fake.pyint(min_value=1, max_value=1000)
    gateway_payment_id = fake.pystr()
    amount = fake_decimal(min_value=10, max_value=10000)

    mock_payment = PaymentInDB(
        payment_id=payment_id,
        order_id=order_id,
        status='approved',
        amount=amount,
        gateway_payment_id=gateway_payment_id,
        token=None,
        authorization=None,
        payment_method=None,
        payment_gateway=None,
        amount_with_fee=None,
        freight_amount=None,
    )
    mocker.patch('app.payment.services.get_payment', return_value=mock_payment)

    # Act
    response = await async_client.get(f'/payment/{gateway_payment_id}')

    # Assert
    assert response.status_code == 200
    assert response.json()['gateway_payment_id'] == gateway_payment_id
