import logging
import sys
from fastapi.responses import JSONResponse

import sentry_sdk
from app.entities.cart import ProductNotFoundError
from app.entities.coupon import CouponDontMatchWithUserError, CouponNotFoundError
from app.entities.user import CredentialError, UserDuplicateError
from app.infra.freight.correios_br import CorreiosInvalidReturnError
from app.infra.payment_gateway.mercadopago_gateway import CardAlreadyUseError
from config import settings
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.infra.endpoints.mail import mail
from app.infra.endpoints.order import order
from app.infra.endpoints.product import product
from app.infra.endpoints.catalog import catalog
from app.infra.endpoints.shipping import shipping
from app.infra.endpoints.users import user
from app.infra.endpoints.payment import payment
from app.infra.endpoints.cart import cart
from app.infra.endpoints.default import (
    inventory,
    reviews,
    coupons,
    campaing,
    sales,
)
from app.infra.endpoints.report import report
from app.mail.tasks import task_message_bus
from app.cart.tasks import task_message_bus # noqa: F811
from app.report.tasks import task_message_bus # noqa: F811
from app.entities.product import ProductSoldOutError
from collections import defaultdict

app = FastAPI(lifespan=task_message_bus.lifespan_context)

request_counts = defaultdict(int)


def rate_limit_exceeded(ip: str, limit: int) -> bool:
    """Check hit limit."""
    return request_counts[ip] > limit


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to hit limit."""
    ip = request.client.host
    if rate_limit_exceeded(ip, limit=10):
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
    request_counts[ip] += 1
    return await call_next(request)

class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


app.mount('/static', StaticFiles(directory='static'), name='static')

origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    settings.FRONTEND_URLS,
]

logger.info(f'Environment: {settings.ENVIRONMENT}')
if settings.ENVIRONMENT == 'production':
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )

app.add_middleware(SentryAsgiMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(ProductNotFoundError)
async def product_not_found_exception_handler(
    _: Request,
    exc: ProductNotFoundError,
) -> JSONResponse:
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

# set loguru format for root logger
logging.getLogger().handlers = [InterceptHandler()]

# logging properties are defined in config.py
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    level=settings.LOG_LEVEL,
    format='{time} {level} {message}',
    backtrace=settings.LOG_BACKTRACE,
    enqueue=True,
    diagnose=True,
)

logging.getLogger('uvicorn.access').handlers = [InterceptHandler()]

app.include_router(user)
app.include_router(payment)
app.include_router(shipping)
app.include_router(order)
app.include_router(mail)
app.include_router(product)
app.include_router(catalog)
app.include_router(cart)
app.include_router(inventory)
app.include_router(reviews)
app.include_router(coupons)
app.include_router(report)
app.include_router(campaing)
app.include_router(sales)
app.include_router(task_message_bus)


def create_app():
    app = FastAPI()
    origins = [
        'localhost',
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    # app.include_router(
    #     payment,
    return app
