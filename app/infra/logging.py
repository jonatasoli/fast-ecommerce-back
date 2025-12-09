"""Logging configuration module."""
import logging
import sys

from loguru import logger

from config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


def setup_logging() -> None:
    """Configure logging with loguru."""
    logging.getLogger().handlers = [InterceptHandler()]

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

    logging.getLogger('opentelemetry').setLevel(logging.DEBUG)

