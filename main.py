import logging
import sys
from fastapi.responses import JSONResponse

import sentry_sdk
from app.entities.cart import ProductNotFoundError
from app.infra.payment_gateway.mercadopago_gateway import CardAlreadyUseError
from config import settings
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.infra.endpoints.direct_sales import direct_sales
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
from app.cart.tasks import task_message_bus
from app.payment.tasks import task_message_bus
from app.infra.worker import task_message_bus

app = FastAPI(lifespan=task_message_bus.lifespan_context)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())

app.mount('/static', StaticFiles(directory='static'), name='static')

origins = [
    'http://localhost:3000',
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
async def product_not_found_exception_handler(_: Request, exc: ProductNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'message': f'{exc.args[0]}'},
    )

@app.exception_handler(CardAlreadyUseError)
async def card_already_use_exception_handler(_: Request, exc: CardAlreadyUseError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'message': f'{exc.args[0]}'},
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
app.include_router(
    direct_sales,
    prefix='/direct-sales',
    responses={404: {'description': 'URL Not found'}},
)
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
