"""Error handlers module."""
from fastapi import Request, status
from fastapi.responses import JSONResponse

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
from app.infra.freight.correios_br import CorreiosInvalidReturnError
from app.infra.payment_gateway.mercadopago_gateway import CardAlreadyUseError


def register_error_handlers(app) -> None:
    """Register all error handlers for the FastAPI app."""

    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_exception_handler(
        _: Request,
        exc: ProductNotFoundError,
    ) -> JSONResponse:
        """Handle ProductNotFoundError."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'message': f'{exc.args[0]}'},
        )

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

    @app.exception_handler(ProductSoldOutError)
    async def product_sold_out_exception_handler(
        _: Request,
        exc: ProductSoldOutError,
    ) -> JSONResponse:
        """Capture ProductSoldOut and raise status code 404."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                'detail': 'Product Sold Out.',
                'stackerror': f'{exc.args[0]}',
            },
        )

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

