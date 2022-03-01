import logging
import re
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

logger = logging.getLogger(__file__)

class SolarWindsFormat(textmap.TextMapPropagator):
    """Extracts and injects SolarWinds tracestate header

    See also https://www.w3.org/TR/trace-context-1/
    """
    _TRACEPARENT_HEADER_NAME = "traceparent"
    _TRACESTATE_HEADER_NAME = "tracestate"
    _TRACEPARENT_HEADER_FORMAT = (
        "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
        + "(-.*)?[ \t]*$"
    )
    _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)

    def extract(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        getter: textmap.Getter = textmap.default_getter,
    ) -> Context:
        """Extracts sw tracestate from carrier into SpanContext
        
        Must be used in composite with TraceContextTextMapPropagator"""
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects sw tracestate from SpanContext into carrier for HTTP request

        See also: https://www.w3.org/TR/trace-context-1/#mutating-the-tracestate-field
        """
        # TODO: Are basic validity checks necessary if this is always used
        #       in composite with TraceContextTextMapPropagator?
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        span_id = self.format_span_id(span_context.span_id)
        trace_flags = self.format_trace_flags(span_context.trace_flags)
        trace_state = span_context.trace_state

        # Prepare carrier with context's or new tracestate
        if trace_state:
            # Check if trace_state already contains sw KV
            if "sw" in trace_state.keys():

                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug(f"Updating trace state with {span_id}-{trace_flags}")
                
                # TODO: Python OTEL TraceState update isn't working
                # trace_state.update("sw", f"{span_id}-{trace_flags}")

                ## Temp: Manual trace_state update
                from collections import OrderedDict
                prev_state = OrderedDict(trace_state.items())
                logger.debug(f"prev_state is {prev_state}")
                prev_state["sw"] = f"{span_id}-{trace_flags}"
                logger.debug(f"Updated prev_state is {prev_state}")
                prev_state.move_to_end("sw", last=False)
                logger.debug(f"Reordered prev_state is {prev_state}")
                new_state = list(prev_state.items())
                logger.debug(f"new_state list is {new_state}")
                trace_state = TraceState(new_state)

            else:
                # If not, add sw KV to beginning of list
                logger.debug(f"Adding KV to trace state with {span_id}-{trace_flags}")
                trace_state.add("sw", f"{span_id}-{trace_flags}")
        else:
            logger.debug(f"Creating new trace state with {span_id}-{trace_flags}")
            trace_state = TraceState([("sw", f"{span_id}-{trace_flags}")])

        setter.set(
            carrier, self._TRACESTATE_HEADER_NAME, trace_state.to_header()
        )

    @property
    def fields(self) -> typing.Set[str]:
        """Returns a set with the fields set in `inject`"""
        return {self._TRACEPARENT_HEADER_NAME, self._TRACESTATE_HEADER_NAME}

    def format_span_id(self, span_id: int) -> str:
        """Formats span ID as 16-byte hexadecimal string"""
        return format(span_id, "016x")

    def format_trace_flags(self, trace_flags: int) -> str:
        """Formats trace flags as 8-bit field"""
        return format(trace_flags, "02x")
