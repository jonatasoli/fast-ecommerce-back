"""Error handlers module."""
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.entities.cart import (
    CartNotFoundError,
    CheckoutProcessingError,
    CouponLimitPriceError,
    InvalidCartUUIDError,
)
from app.entities.category import CategoryMediaNotFoundError, CategoryNotFoundError
from app.entities.coupon import CouponDontMatchWithUserError, CouponNotFoundError
from app.entities.payment import PaymentNotFoundError
from app.entities.product import ProductNotFoundError, ProductSoldOutError
from app.entities.user import CredentialError, UserDuplicateError
from app.infra.freight.correios_br import CorreiosInvalidReturnError
from app.infra.payment_gateway.mercadopago_gateway import CardAlreadyUseError


def _register_product_not_found_handler(app) -> None:
    """Register ProductNotFoundError handler."""

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_exception_handler(
        _: Request,
        exc: ProductNotFoundError,
    ) -> JSONResponse:
        """Handle ProductNotFoundError."""
        message = exc.args[0] if exc.args else 'Product not found'
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': message},
        )


def _register_card_already_use_handler(app) -> None:
    """Register CardAlreadyUseError handler."""

    @app.exception_handler(CardAlreadyUseError)
    async def card_already_use_exception_handler(
        _: Request,
        exc: CardAlreadyUseError,
    ) -> JSONResponse:
        """Capture CardAlreadyUseError and raise status code 409."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={'message': f'{exc.args[0]}'},
        )


def _register_credential_error_handler(app) -> None:
    """Register CredentialError handler."""

    @app.exception_handler(CredentialError)
    async def credential_exception_handler(
        _: Request,
        exc: CredentialError,
    ) -> JSONResponse:
        """Capture CredentialError and raise status code 401."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                'detail': 'Incorrect username or password',
            },
        )


def _register_product_sold_out_handler(app) -> None:
    """Register ProductSoldOutError handler."""

    @app.exception_handler(ProductSoldOutError)
    async def product_sold_out_exception_handler(
        _: Request,
        exc: ProductSoldOutError,
    ) -> JSONResponse:
        """Capture ProductSoldOut and raise status code 404."""
        stackerror = exc.args[0] if exc.args else 'There are products in not inventory.'
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': 'Product Sold Out.',
                'stackerror': stackerror,
            },
        )


def _register_coupon_not_found_handler(app) -> None:
    """Register CouponNotFoundError handler."""

    @app.exception_handler(CouponNotFoundError)
    async def coupon_not_found_handler(
        _: Request,
        exc: CouponNotFoundError,
    ) -> JSONResponse:
        """Coupon not valid error raise status code 404."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': 'Invalid Coupon.',
            },
        )


def _register_correios_error_handler(app) -> None:
    """Register CorreiosInvalidReturnError handler."""

    @app.exception_handler(CorreiosInvalidReturnError)
    async def correios_api_error_handler(
        _: Request,
        exc: CorreiosInvalidReturnError,
    ) -> JSONResponse:
        """Correios api Error raise status code 404."""
        match exc.args[0]:
            case 'PRC-101':
                msg = 'ZipCode invalid'
            case 'PRZ-101':
                msg = 'ZipCode invalid'
            case _:
                msg = exc.args[0]
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': f'Correios API return error. {msg}',
                'code': exc.args[0],
                'reason': msg,
            },
        )


def _register_user_duplicate_handler(app) -> None:
    """Register UserDuplicateError handler."""

    @app.exception_handler(UserDuplicateError)
    async def user_already_signup(
        _: Request,
        exc: UserDuplicateError,
    ) -> JSONResponse:
        """User already signup raise status code 409."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'detail': 'User already sign up.',
            },
        )


def _register_coupon_dont_match_handler(app) -> None:
    """Register CouponDontMatchWithUserError handler."""

    @app.exception_handler(CouponDontMatchWithUserError)
    async def user_dont_match_with_coupon(
        _: Request,
        exc: CouponDontMatchWithUserError,
    ) -> JSONResponse:
        """User don't match with coupon user_id raise status code 409."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                'detail': 'Coupon is invalid for this user.',
            },
        )


def _register_coupon_limit_error_handler(app) -> None:
    """Register CouponLimitPriceError handler."""

    @app.exception_handler(CouponLimitPriceError)
    async def coupon_limit_error(
        _: Request,
        exc: CouponLimitPriceError,
    ) -> JSONResponse:
        """User don't match with coupon user_id raise status code 409."""
        conflict_with_coupon = 439
        return JSONResponse(
            status_code=conflict_with_coupon,
            content={
                'detail': 'Coupon is not accepable for this preconditions.',
            },
        )


def _register_checkout_processing_error_handler(app) -> None:
    """Register CheckoutProcessingError handler."""

    @app.exception_handler(CheckoutProcessingError)
    async def checkout_processor_error(
        _: Request,
        exc: CheckoutProcessingError,
    ) -> JSONResponse:
        """Problem with checkout service."""
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                'detail': 'Error with checkout service.',
            },
        )


def _register_payment_not_found_handler(app) -> None:
    """Register PaymentNotFoundError handler."""

    @app.exception_handler(PaymentNotFoundError)
    async def payment_not_found_error(
        _: Request,
        exc: PaymentNotFoundError,
    ) -> JSONResponse:
        """Problem with checkout service."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': 'Payment not found in gateway system.',
            },
        )


def _register_invalid_cart_uuid_handler(app) -> None:
    """Register InvalidCartUUIDError handler."""

    @app.exception_handler(InvalidCartUUIDError)
    async def cart_uuid_invalid(
        _: Request,
        exc: InvalidCartUUIDError,
    ) -> JSONResponse:
        """Problem with invalid UUID in cart."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                'detail': 'Cart UUID invalid or with conflict.',
            },
        )


def _register_cart_not_found_handler(app) -> None:
    """Register CartNotFoundError handler."""

    @app.exception_handler(CartNotFoundError)
    async def cart_not_found(
        _: Request,
        exc: CartNotFoundError,
    ) -> JSONResponse:
        """Cart not found in cache or database."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'detail': 'Cart not found'},
        )


def _register_category_not_found_handler(app) -> None:
    """Register CategoryNotFoundError handler."""

    @app.exception_handler(CategoryNotFoundError)
    async def category_not_found_handler(
        _: Request,
        exc: CategoryNotFoundError,
    ) -> JSONResponse:
        """Category not found error raise status code 404."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': exc.message,
            },
        )


def _register_category_media_not_found_handler(app) -> None:
    """Register CategoryMediaNotFoundError handler."""

    @app.exception_handler(CategoryMediaNotFoundError)
    async def category_media_not_found_handler(
        _: Request,
        exc: CategoryMediaNotFoundError,
    ) -> JSONResponse:
        """Category media not found error raise status code 404."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': exc.message,
            },
        )


def register_error_handlers(app) -> None:
    """Register all error handlers for the FastAPI app."""
    _register_product_not_found_handler(app)
    _register_card_already_use_handler(app)
    _register_credential_error_handler(app)
    _register_product_sold_out_handler(app)
    _register_coupon_not_found_handler(app)
    _register_correios_error_handler(app)
    _register_user_duplicate_handler(app)
    _register_coupon_dont_match_handler(app)
    _register_coupon_limit_error_handler(app)
    _register_checkout_processing_error_handler(app)
    _register_payment_not_found_handler(app)
    _register_invalid_cart_uuid_handler(app)
    _register_cart_not_found_handler(app)
    _register_category_not_found_handler(app)
    _register_category_media_not_found_handler(app)
