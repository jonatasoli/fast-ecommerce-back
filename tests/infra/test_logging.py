"""Tests for logging module."""
import logging

import pytest
from loguru import logger

from app.infra.logging import InterceptHandler, setup_logging


def test_intercept_handler_emit(caplog):
    """Test InterceptHandler emits log records correctly."""
    # Setup
    handler = InterceptHandler()
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message',
        args=(),
        exc_info=None,
    )

    # Act
    handler.emit(record)

    # Assert
    assert len(logger._core.handlers) > 0


def test_setup_logging():
    """Test setup_logging configures logging correctly."""
    # Setup
    original_handlers = logging.getLogger().handlers.copy()

    try:
        # Act
        setup_logging()

        # Assert
        root_handlers = logging.getLogger().handlers
        assert any(isinstance(h, InterceptHandler) for h in root_handlers)

        uvicorn_handlers = logging.getLogger('uvicorn.access').handlers
        assert any(isinstance(h, InterceptHandler) for h in uvicorn_handlers)

        assert logging.getLogger('opentelemetry').level == logging.DEBUG
    finally:
        logging.getLogger().handlers = original_handlers
