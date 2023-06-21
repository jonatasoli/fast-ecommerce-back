import logging
import sys

import sentry_sdk
from dynaconf import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from endpoints.v1.direct_sales import direct_sales
from endpoints.v1.mail import mail
from endpoints.v1.order import order
from endpoints.v1.product import product
from endpoints.v1.product import catalog
from endpoints.v1.shipping import shipping
from endpoints.v1.users import user
from endpoints.v1.payment import payment
from endpoints.v1.payment import cart
from endpoints.v1.default import (
    inventory,
    reviews,
    coupons,
    reports,
    campaing,
    sales,
)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

origins = [
    '*',
]

sentry_sdk.init(
    'https://f8ca28ef3c3a4b54aac3a61c963a043b@o281685.ingest.sentry.io/5651868',
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
    responses={404: {'description': 'Not found'}},
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
app.include_router(reports)
app.include_router(campaing)
app.include_router(sales)

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
    #     responses={status.HTTP_404_NOT_FOUND: {'description': 'Not found'}},
    # )
    return app
