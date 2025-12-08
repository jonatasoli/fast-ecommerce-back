"""Tests for CORS module."""
import pytest
from config import settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infra.cors import get_cors_origins, setup_cors


def test_get_cors_origins_with_cors_origins_env(monkeypatch):
    """Test get_cors_origins with CORS_ORIGINS environment variable."""
    # Setup
    monkeypatch.setattr(settings, 'CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://frontend.com')
    monkeypatch.setattr(settings, 'ADMIN_URL', 'https://admin.com')

    # Act
    origins = get_cors_origins()

    # Assert
    assert 'http://localhost:3000' in origins
    assert 'http://localhost:5173' in origins
    assert 'https://frontend.com' in origins
    assert 'https://admin.com' in origins


def test_get_cors_origins_without_cors_origins_env(monkeypatch):
    """Test get_cors_origins without CORS_ORIGINS environment variable."""
    # Setup
    monkeypatch.delattr(settings, 'CORS_ORIGINS', raising=False)
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://frontend.com')
    monkeypatch.setattr(settings, 'ADMIN_URL', 'https://admin.com')

    # Act
    origins = get_cors_origins()

    # Assert
    assert 'https://frontend.com' in origins
    assert 'https://admin.com' in origins


def test_get_cors_origins_empty(monkeypatch):
    """Test get_cors_origins with empty settings."""
    # Setup
    monkeypatch.delattr(settings, 'CORS_ORIGINS', raising=False)
    monkeypatch.delattr(settings, 'FRONTEND_URL', raising=False)
    monkeypatch.delattr(settings, 'ADMIN_URL', raising=False)

    # Act
    origins = get_cors_origins()

    # Assert
    assert origins == []


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

    # Assert
    assert response.status_code == 200
