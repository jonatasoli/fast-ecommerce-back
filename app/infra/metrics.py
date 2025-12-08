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

    Only configures metrics and tracing in production environment.
    """
    if not (hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production'):
        return

    resource_attributes = {
        'service.name': 'api-gattorosa',
        'service.version': os.getenv('SERVICE_VERSION', '0.2.1'),
        'deployment.environment': settings.ENVIRONMENT,
    }

    resource = Resource.create(resource_attributes)

    tracer_provider = trace.get_tracer_provider()
    if not isinstance(tracer_provider, TracerProvider):
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

    jaeger_host = getattr(settings, 'SENTRY_DSN', 'localhost')
    jaeger_endpoint = f'http://{jaeger_host}:14268/api/traces'

    jaeger_exporter = JaegerExporter(
        collector_endpoint=jaeger_endpoint,
    )
    logger.info(f'✅ Jaeger HTTP exporter configured: {jaeger_endpoint}')
    tracer_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter),
    )

    FastAPIInstrumentor.instrument_app(app)

    logging.getLogger('opentelemetry').setLevel(logging.DEBUG)
