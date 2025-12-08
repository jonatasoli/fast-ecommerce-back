# ruff: noqa: I001
import pytest
from unittest.mock import AsyncMock
from app.entities.coupon import CouponInDB, CouponCreate, CouponUpdate
from decimal import Decimal


@pytest.mark.asyncio
async def test_get_coupons_should_return_list(async_client, mocker, async_admin_token):
    # Setup
    mock_coupons = [
        CouponInDB(
            coupon_id=1,
            code='TEST1',
            discount=Decimal('10'),
            discount_type='percent',
            active=True,
            qty=100,
        ),
        CouponInDB(
            coupon_id=2,
            code='TEST2',
            discount=Decimal('20'),
            discount_type='fixed',
            active=True,
            qty=50,
        ),
    ]
    mocker.patch('app.coupons.repository.get_coupons', return_value=mock_coupons)
    mocker.patch('app.infra.endpoints.coupon.verify_admin', return_value=True)

    # Act
    response = await async_client.get(
        '/coupon/', headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['code'] == 'TEST1'


@pytest.mark.asyncio
async def test_get_coupon_should_return_coupon(async_client, mocker, async_admin_token):
    # Setup
    mock_coupon = CouponInDB(
        coupon_id=1,
        code='TEST1',
        discount=Decimal('10'),
        discount_type='percent',
        active=True,
        qty=100,
    )
    mocker.patch('app.coupons.repository.get_coupon', return_value=mock_coupon)
    mocker.patch('app.infra.endpoints.coupon.verify_admin', return_value=True)

    # Act
    response = await async_client.get(
        '/coupon/1', headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['code'] == 'TEST1'


@pytest.mark.asyncio
async def test_create_coupon_should_create(async_client, mocker, async_admin_token):
    # Setup
    mocker.patch('app.infra.endpoints.coupon.verify_admin', return_value=True)
    payload = {
        'code': 'NEWCOUPON',
        'discount': 15.5,
        'qty': 100,
        'active': True,
    }

    # Act
    response = await async_client.post(
        '/coupon/',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 201
    assert response.json()['code'] == 'NEWCOUPON'


@pytest.mark.asyncio
async def test_update_coupon_should_update(async_client, mocker, async_admin_token):
    # Setup
    mock_coupon = CouponInDB(
        coupon_id=1,
        code='UPDATED',
        discount=Decimal('10'),
        discount_type='percent',
        active=True,
        qty=100,
    )
    mocker.patch('app.coupons.repository.update_coupon', return_value=mock_coupon)
    mocker.patch('app.infra.endpoints.coupon.verify_admin', return_value=True)
    payload = {'code': 'UPDATED', 'discount': 10.0}

    # Act
    response = await async_client.patch(
        '/coupon/1',
        json=payload,
        headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()['code'] == 'UPDATED'


@pytest.mark.asyncio
async def test_delete_coupon_should_delete(async_client, mocker, async_admin_token):
    # Setup
    mocker.patch('app.coupons.repository.delete_coupon', return_value=True)
    mocker.patch('app.infra.endpoints.coupon.verify_admin', return_value=True)

    # Act
    response = await async_client.delete(
        '/coupon/1', headers={'Authorization': f'Bearer {async_admin_token}'},
    )

    # Assert
    assert response.status_code == 204
