import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME

logger = logging.getLogger(__name__)


def setup_tracing(app: FastAPI) -> None:
    if not OTEL_EXPORTER_OTLP_ENDPOINT:
        return
    provider = TracerProvider(
        resource=Resource.create({"service.name": OTEL_SERVICE_NAME}),
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True),
        )
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    logger.info("tracing enabled endpoint=%s", OTEL_EXPORTER_OTLP_ENDPOINT)
