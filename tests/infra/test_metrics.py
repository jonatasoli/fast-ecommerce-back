"""Tests for metrics module."""
import pytest
from config import settings
from fastapi import FastAPI

from app.infra.metrics import setup_metrics


def test_setup_metrics_development(monkeypatch):
    """Test setup_metrics in development environment."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'development')
    app = FastAPI()

    # Act
    setup_metrics(app)

    # Assert
    assert app is not None


def test_setup_metrics_production(monkeypatch):
    """Test setup_metrics in production environment."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'production')
    monkeypatch.setattr(settings, 'SENTRY_DSN', 'localhost:14268')
    app = FastAPI()

    # Act
    setup_metrics(app)

    # Assert
    assert app is not None
