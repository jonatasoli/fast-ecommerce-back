"""Metrics and OpenTelemetry configuration module."""
import logging
import os

from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import settings


def setup_metrics(app) -> None:
    """Configure OpenTelemetry metrics and tracing.

    Following OpenTelemetry stability guidelines:
    https://opentelemetry.io/docs/specs/otel/versioning-and-stability/#stable

    The TracerProvider is configured once and reused. The API stability
    is maintained by ensuring backward compatibility.
    """
    resource_attributes = {
        'service.name': 'api-gattorosa',
        'service.version': os.getenv('SERVICE_VERSION', '0.2.1'),
    }

    if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT:
        resource_attributes['deployment.environment'] = settings.ENVIRONMENT

    resource = Resource.create(resource_attributes)

    tracer_provider = trace.get_tracer_provider()
    if not isinstance(tracer_provider, TracerProvider):
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

    # Configure exporter only in production
    if settings.ENVIRONMENT == 'production':
        jaeger_exporter = JaegerExporter(
            collector_endpoint=f'http://{settings.SENTRY_DSN}:14268/api/tempo',
        )
        logger.info('✅ Jaeger HTTP exporter configured for Tempo')
        tracer_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter),
        )

    # Instrument FastAPI app
    FastAPIInstrumentor.instrument_app(app)

    # Set opentelemetry logging level
    logging.getLogger('opentelemetry').setLevel(logging.DEBUG)
