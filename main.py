"""Main application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.infra.endpoints.cart import cart
from app.infra.endpoints.catalog import catalog
from app.infra.endpoints.coupon import coupon
from app.infra.endpoints.crowdfunding import crowdfunding
from app.infra.endpoints.default import (
    campaing,
    inventory,
    reviews,
    sales,
)
from app.infra.endpoints.mail import mail
from app.infra.endpoints.order import order
from app.infra.endpoints.payment import payment
from app.infra.endpoints.product import product
from app.infra.endpoints.report import report
from app.infra.endpoints.settings import settings as settingsconfig
from app.infra.endpoints.shipping import shipping
from app.infra.endpoints.users import user, users
from app.infra.error_handlers import register_error_handlers
from app.infra.cors import setup_cors
from app.infra.logging import setup_logging
from app.infra.metrics import setup_metrics
from app.infra.worker import task_message_bus

from app.mail.tasks import task_message_bus  # noqa: F401
from app.cart.tasks import task_message_bus  # noqa: F811
from app.report.tasks import task_message_bus  # noqa: F811


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Setup logging first
    setup_logging()

    # Create FastAPI app
    app = FastAPI()

    # Mount static files
    app.mount('/static', StaticFiles(directory='static'), name='static')

    # Setup CORS
    setup_cors(app)

    # Register error handlers
    register_error_handlers(app)

    # Setup metrics and OpenTelemetry
    setup_metrics(app)

    # Include routers
    app.include_router(user)
    app.include_router(users)
    app.include_router(payment)
    app.include_router(shipping)
    app.include_router(order)
    app.include_router(mail)
    app.include_router(product)
    app.include_router(catalog)
    app.include_router(cart)
    app.include_router(inventory)
    app.include_router(reviews)
    app.include_router(coupon)
    app.include_router(report)
    app.include_router(campaing)
    app.include_router(sales)
    app.include_router(crowdfunding)
    app.include_router(task_message_bus)
    app.include_router(settingsconfig)

    return app


app = create_app()
