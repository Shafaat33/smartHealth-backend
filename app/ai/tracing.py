from contextlib import contextmanager

from opentelemetry import trace

_tracer = trace.get_tracer("smarthealth.assistant")


@contextmanager
def assistant_span(name: str, **attributes):
    with _tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield span
