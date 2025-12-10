"""Tests for metrics module."""
import logging
import os

import pytest
from config import settings
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from app.infra.metrics import setup_metrics


def test_setup_metrics_development(monkeypatch):
    """Test setup_metrics in development environment does nothing."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'development')
    app = FastAPI()
    original_provider = trace.get_tracer_provider()

    # Act
    setup_metrics(app)

    assert app is not None
    assert trace.get_tracer_provider() == original_provider


def test_setup_metrics_testing(monkeypatch):
    """Test setup_metrics in testing environment does nothing."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'testing')
    app = FastAPI()
    original_provider = trace.get_tracer_provider()

    # Act
    setup_metrics(app)

    assert app is not None
    assert trace.get_tracer_provider() == original_provider


def test_setup_metrics_no_environment(monkeypatch):
    """Test setup_metrics when ENVIRONMENT is not set."""
    # Setup
    if hasattr(settings, 'ENVIRONMENT'):
        monkeypatch.delattr(settings, 'ENVIRONMENT', raising=False)
    app = FastAPI()
    original_provider = trace.get_tracer_provider()

    # Act
    setup_metrics(app)

    assert app is not None
    assert trace.get_tracer_provider() == original_provider

def test_setup_metrics_production(monkeypatch):
    """Test setup_metrics in production environment."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'production')
    monkeypatch.setattr(settings, 'SENTRY_DSN', 'localhost')
    app = FastAPI()
    monkeypatch.setenv('SERVICE_VERSION', '1.0.0')

    # Act
    setup_metrics(app)

    assert app is not None
    tracer_provider = trace.get_tracer_provider()
    assert isinstance(tracer_provider, TracerProvider)
    assert logging.getLogger('opentelemetry').level == logging.DEBUG


def test_setup_metrics_production_with_default_version(monkeypatch):
    """Test setup_metrics in production with default service version."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'production')
    monkeypatch.setattr(settings, 'SENTRY_DSN', 'jaeger.example.com')
    app = FastAPI()
    monkeypatch.delenv('SERVICE_VERSION', raising=False)

    # Act
    setup_metrics(app)

    assert app is not None
    tracer_provider = trace.get_tracer_provider()
    assert isinstance(tracer_provider, TracerProvider)
    resource = tracer_provider.resource
    assert resource is not None
    assert 'service.name' in resource.attributes


def test_setup_metrics_production_with_custom_version(monkeypatch):
    """Test setup_metrics in production with custom service version."""
    # Setup
    monkeypatch.setattr(settings, 'ENVIRONMENT', 'production')
    monkeypatch.setattr(settings, 'SENTRY_DSN', 'localhost')
    app = FastAPI()
    custom_version = '2.0.0'
    monkeypatch.setenv('SERVICE_VERSION', custom_version)

    # Act
    setup_metrics(app)

    assert app is not None
    tracer_provider = trace.get_tracer_provider()
    assert isinstance(tracer_provider, TracerProvider)
    resource = tracer_provider.resource
    assert resource is not None
    assert 'service.name' in resource.attributes
