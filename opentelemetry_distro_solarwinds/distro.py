"""Module to configure OpenTelemetry agent to work with SolarWinds backend"""

from opentelemetry import trace
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.propagators import set_global_response_propagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry_distro_solarwinds.exporter import SolarWindsSpanExporter
from opentelemetry_distro_solarwinds.response_propagator import SolarWindsTraceResponsePropagator
from opentelemetry_distro_solarwinds.sampler import ParentBasedSwSampler


class SolarWindsDistro(BaseDistro):
    """SolarWinds custom distro for OpenTelemetry agents.

    With this custom distro, the following functionality is introduced:
        - no functionality added at this time
    """
    def _configure(self, **kwargs):
        # Automatically make use of custom SolarWinds sampler
        trace.set_tracer_provider(
            TracerProvider(sampler=ParentBasedSwSampler()))
        # Automatically configure the SolarWinds Span exporter
        span_exporter = BatchSpanProcessor(SolarWindsSpanExporter())
        trace.get_tracer_provider().add_span_processor(span_exporter)
        # Set global HTTP response propagator
        set_global_response_propagator(SolarWindsTraceResponsePropagator())