import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.v1.users import user
from endpoints.v1.payment import payment
from endpoints.v1.direct_sales import direct_sales

from dynaconf import settings
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# set loguru format for root logger
logging.getLogger().handlers = [InterceptHandler()]

# logging properties are defined in config.py
logger.start(
        sys.stdout,
        colorize=True,
        level=settings.LOG_LEVEL,
        format="{time} {level} {message}",
        backtrace=settings.LOG_BACKTRACE,
        enqueue=True,
        diagnose=True
        )

logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]

app.include_router(user)
app.include_router(payment)
app.include_router(
        direct_sales,
        prefix="/direct-sales",
        responses={404: {"description": "Not found"}})

