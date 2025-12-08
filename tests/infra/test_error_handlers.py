"""Tests for error handlers module."""
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.entities.cart import (
    CheckoutProcessingError,
    CouponLimitPriceError,
    InvalidCartUUIDError,
)
from app.entities.category import CategoryMediaNotFoundError, CategoryNotFoundError
from app.entities.coupon import CouponDontMatchWithUserError, CouponNotFoundError
from app.entities.payment import PaymentNotFoundError
from app.entities.product import ProductNotFoundError, ProductSoldOutError
from app.entities.user import CredentialError, UserDuplicateError
from app.infra.error_handlers import register_error_handlers
from app.infra.freight.correios_br import CorreiosInvalidReturnError
from app.infra.payment_gateway.mercadopago_gateway import CardAlreadyUseError


@pytest.fixture
def app_with_handlers():
    """Create FastAPI app with error handlers registered."""
    app = FastAPI()
    register_error_handlers(app)
    return app


@pytest.fixture
def client(app_with_handlers):
    """Create test client."""
    return TestClient(app_with_handlers)


def test_product_not_found_handler(client, app_with_handlers):
    """Test ProductNotFoundError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise ProductNotFoundError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert 'message' in data or 'detail' in data


def test_card_already_use_handler(client, app_with_handlers):
    """Test CardAlreadyUseError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CardAlreadyUseError('Card already in use')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert 'message' in response.json()


def test_credential_error_handler(client, app_with_handlers):
    """Test CredentialError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CredentialError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == 'Incorrect username or password'


def test_product_sold_out_handler(client, app_with_handlers):
    """Test ProductSoldOutError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise ProductSoldOutError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data.get('detail') == 'Product Sold Out.' or 'Product Sold Out' in str(data.get('detail', ''))


def test_coupon_not_found_handler(client, app_with_handlers):
    """Test CouponNotFoundError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CouponNotFoundError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Invalid Coupon.'


def test_correios_error_handler_prc_101(client, app_with_handlers):
    """Test CorreiosInvalidReturnError handler with PRC-101."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CorreiosInvalidReturnError('PRC-101')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'ZipCode invalid' in response.json()['detail']
    assert response.json()['code'] == 'PRC-101'


def test_correios_error_handler_prz_101(client, app_with_handlers):
    """Test CorreiosInvalidReturnError handler with PRZ-101."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CorreiosInvalidReturnError('PRZ-101')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert 'ZipCode invalid' in response.json()['detail']
    assert response.json()['code'] == 'PRZ-101'


def test_correios_error_handler_other(client, app_with_handlers):
    """Test CorreiosInvalidReturnError handler with other error."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CorreiosInvalidReturnError('OTHER-ERROR')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['code'] == 'OTHER-ERROR'


def test_user_duplicate_error_handler(client, app_with_handlers):
    """Test UserDuplicateError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise UserDuplicateError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()['detail'] == 'User already sign up.'


def test_coupon_dont_match_error_handler(client, app_with_handlers):
    """Test CouponDontMatchWithUserError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CouponDontMatchWithUserError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()['detail'] == 'Coupon is invalid for this user.'


def test_coupon_limit_error_handler(client, app_with_handlers):
    """Test CouponLimitPriceError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CouponLimitPriceError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == 439
    assert 'Coupon is not accepable' in response.json()['detail']


def test_checkout_processing_error_handler(client, app_with_handlers):
    """Test CheckoutProcessingError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CheckoutProcessingError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()['detail'] == 'Error with checkout service.'


def test_payment_not_found_error_handler(client, app_with_handlers):
    """Test PaymentNotFoundError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise PaymentNotFoundError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Payment not found in gateway system.'


def test_invalid_cart_uuid_error_handler(client, app_with_handlers):
    """Test InvalidCartUUIDError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise InvalidCartUUIDError()

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == 'Cart UUID invalid or with conflict.'


def test_category_not_found_handler(client, app_with_handlers):
    """Test CategoryNotFoundError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CategoryNotFoundError('Category not found')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Category not found'


def test_category_media_not_found_handler(client, app_with_handlers):
    """Test CategoryMediaNotFoundError handler."""
    # Setup
    @app_with_handlers.get('/test')
    async def test_route():
        raise CategoryMediaNotFoundError('Media not found')

    # Act
    response = client.get('/test')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()['detail'] == 'Media not found'
