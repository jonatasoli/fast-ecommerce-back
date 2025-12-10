"""Tests for CORS module."""
import pytest
from config import settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infra.cors import get_cors_origins, setup_cors


def test_get_cors_origins_with_cors_origins_env(monkeypatch):
    """Test get_cors_origins with CORS_ORIGINS environment variable."""
    # Setup
    original_cors = getattr(settings, 'CORS_ORIGINS', None)
    original_frontend = getattr(settings, 'FRONTEND_URL', None)
    original_admin = getattr(settings, 'ADMIN_URL', None)

    try:
        object.__setattr__(settings, 'CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
        object.__setattr__(settings, 'FRONTEND_URL', 'https://frontend.com')
        object.__setattr__(settings, 'ADMIN_URL', 'https://admin.com')

        # Act
        origins = get_cors_origins()

        assert 'http://localhost:3000' in origins
        assert 'http://localhost:5173' in origins
        assert 'https://frontend.com' in origins
        assert 'https://admin.com' in origins
    finally:
        if original_cors is not None:
            object.__setattr__(settings, 'CORS_ORIGINS', original_cors)
        elif hasattr(settings, 'CORS_ORIGINS'):
            object.__delattr__(settings, 'CORS_ORIGINS')
        if original_frontend is not None:
            object.__setattr__(settings, 'FRONTEND_URL', original_frontend)
        if original_admin is not None:
            object.__setattr__(settings, 'ADMIN_URL', original_admin)


def test_get_cors_origins_without_cors_origins_env(monkeypatch):
    """Test get_cors_origins without CORS_ORIGINS environment variable."""
    # Setup
    original_cors = getattr(settings, 'CORS_ORIGINS', None)
    original_frontend = getattr(settings, 'FRONTEND_URL', None)
    original_admin = getattr(settings, 'ADMIN_URL', None)

    try:
        if hasattr(settings, 'CORS_ORIGINS'):
            object.__delattr__(settings, 'CORS_ORIGINS')
        object.__setattr__(settings, 'FRONTEND_URL', 'https://frontend.com')
        object.__setattr__(settings, 'ADMIN_URL', 'https://admin.com')

        # Act
        origins = get_cors_origins()

        assert 'https://frontend.com' in origins
        assert 'https://admin.com' in origins
    finally:
        if original_cors is not None:
            object.__setattr__(settings, 'CORS_ORIGINS', original_cors)
        if original_frontend is not None:
            object.__setattr__(settings, 'FRONTEND_URL', original_frontend)
        if original_admin is not None:
            object.__setattr__(settings, 'ADMIN_URL', original_admin)


def test_get_cors_origins_empty(monkeypatch):
    """Test get_cors_origins with empty settings."""
    # Setup
    original_cors = getattr(settings, 'CORS_ORIGINS', None)
    original_frontend = getattr(settings, 'FRONTEND_URL', None)
    original_admin = getattr(settings, 'ADMIN_URL', None)

    try:
        object.__setattr__(settings, 'CORS_ORIGINS', None)
        object.__setattr__(settings, 'FRONTEND_URL', None)
        object.__setattr__(settings, 'ADMIN_URL', None)

        # Act
        origins = get_cors_origins()

        assert origins == []
    finally:
        if original_cors is not None:
            object.__setattr__(settings, 'CORS_ORIGINS', original_cors)
        elif hasattr(settings, 'CORS_ORIGINS'):
            object.__delattr__(settings, 'CORS_ORIGINS')
        if original_frontend is not None:
            object.__setattr__(settings, 'FRONTEND_URL', original_frontend)
        if original_admin is not None:
            object.__setattr__(settings, 'ADMIN_URL', original_admin)


def test_setup_cors():
    """Test setup_cors adds CORS middleware."""
    # Setup
    app = FastAPI()

    @app.get('/test')
    async def test_route():
        return {'message': 'test'}

    setup_cors(app)

    # Act
    client = TestClient(app)
    response = client.get('/test')

    assert response.status_code == 200
