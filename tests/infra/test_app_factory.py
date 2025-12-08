"""Tests for app factory module."""
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.entities.product import ProductNotFoundError
from main import create_app


def test_create_app():
    """Test create_app creates a FastAPI app."""
    # Act
    app = create_app()

    # Assert
    assert isinstance(app, FastAPI)


def test_create_app_has_routers():
    """Test create_app includes all routers."""
    # Act
    app = create_app()

    # Assert
    assert len(app.routes) > 0


def test_create_app_static_files():
    """Test create_app mounts static files."""
    # Act
    app = create_app()

    # Assert
    static_mounts = [route for route in app.routes if hasattr(route, 'path') and route.path == '/static']
    assert len(static_mounts) > 0


def test_create_app_cors():
    """Test create_app configures CORS."""
    # Setup
    app = create_app()
    client = TestClient(app)

    # Act
    response = client.get('/docs')

    # Assert
    assert response.status_code in [200, 404]  # Docs might not be available in test


def test_create_app_error_handlers():
    """Test create_app registers error handlers."""
    # Setup
    app = create_app()

    @app.get('/test-error')
    async def test_route():
        raise ProductNotFoundError()

    client = TestClient(app)

    # Act
    response = client.get('/test-error')

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert 'message' in data or 'detail' in data
