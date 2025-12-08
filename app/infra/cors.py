"""CORS configuration module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings


def get_cors_origins() -> list[str]:
    """Get CORS origins from environment variables."""
    origins = []

    # Add CORS_ORIGINS from environment variable (comma-separated)
    if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS:
        cors_origins = str(settings.CORS_ORIGINS).split(',')
        origins.extend([origin.strip() for origin in cors_origins if origin.strip()])

    # Add FRONTEND_URL and ADMIN_URL if they exist
    if hasattr(settings, 'FRONTEND_URL') and settings.FRONTEND_URL:
        origins.append(settings.FRONTEND_URL)

    if hasattr(settings, 'ADMIN_URL') and settings.ADMIN_URL:
        origins.append(settings.ADMIN_URL)

    return origins


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI app."""
    origins = get_cors_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

