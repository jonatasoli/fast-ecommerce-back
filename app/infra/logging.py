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
    # Set loguru format for root logger
    logging.getLogger().handlers = [InterceptHandler()]

    # Remove default handler
    logger.remove()

    # Add stdout handler
    logger.add(
        sys.stdout,
        colorize=True,
        level=settings.LOG_LEVEL,
        format='{time} {level} {message}',
        backtrace=settings.LOG_BACKTRACE,
        enqueue=True,
        diagnose=True,
    )

    # Intercept uvicorn access logs
    logging.getLogger('uvicorn.access').handlers = [InterceptHandler()]

    # Set opentelemetry logging level
    logging.getLogger('opentelemetry').setLevel(logging.DEBUG)

