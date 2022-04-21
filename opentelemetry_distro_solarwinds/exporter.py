""" This module provides a SolarWinds-specific exporter.

The exporter translates OpenTelemetry spans into AppOptics events so that the instrumentation data
generated by an OpenTelemetry-based agent can be processed by the SolarWinds backend.
"""

import logging
import os

from opentelemetry.sdk.trace.export import SpanExporter

from opentelemetry_distro_solarwinds.extension.oboe import (Context, Metadata,
                                                            Reporter)
from opentelemetry_distro_solarwinds.w3c_transformer import W3CTransformer

logger = logging.getLogger(__file__)


class SolarWindsSpanExporter(SpanExporter):
    """SolarWinds span exporter.

    Reports instrumentation data to the SolarWinds backend.
    """
    def __init__(self, *args, **kw_args):
        super().__init__(*args, **kw_args)
        self.reporter = None
        self._initialize_solarwinds_reporter()

    def export(self, spans):
        """Export to AO events and report via liboboe.

        Note that OpenTelemetry timestamps are in nanoseconds, whereas AppOptics expects timestamps
        to be in microseconds, thus all times need to be divided by 1000.
        """
        for span in spans:
            md = self._build_metadata(span.get_span_context())
            if span.parent and span.parent.is_valid:
                # If there is a parent, we need to add an edge to this parent to this entry event
                logger.debug("Continue trace from {}".format(md.toString()))
                parent_md = self._build_metadata(span.parent)
                evt = Context.createEntry(md, int(span.start_time / 1000),
                                         parent_md)
            else:
                # In OpenTelemrtry, there are no events with individual IDs, but only a span ID
                # and trace ID. Thus, the entry event needs to be generated such that it has the
                # same op ID as the span ID of the OTel span.
                logger.debug("Start a new trace {}".format(md.toString()))
                evt = Context.createEntry(md, int(span.start_time / 1000))
            evt.addInfo('Layer', span.name)
            evt.addInfo('Language', 'Python')
            for k, v in span.attributes.items():
                evt.addInfo(k, v)
            self.reporter.sendReport(evt, False)

            for event in span.events:
                if event.name == 'exception':
                    self._report_exception_event(event)
                else:
                    self._report_info_event(event)

            evt = Context.createExit(int(span.end_time / 1000))
            evt.addInfo('Layer', span.name)
            self.reporter.sendReport(evt, False)

    def _report_exception_event(self, event):
        evt = Context.createEvent(int(event.timestamp / 1000))
        evt.addInfo('Label', 'error')
        evt.addInfo('Spec', 'error')
        evt.addInfo('ErrorClass', event.attributes.get('exception.type', None))
        evt.addInfo('ErrorMsg', event.attributes.get('exception.message',
                                                     None))
        evt.addInfo('Backtrace',
                    event.attributes.get('exception.stacktrace', None))
        # add remaining attributes, if any
        for k, v in event.attributes.items():
            if k not in ('exception.type', 'exception.message',
                         'exception.stacktrace'):
                evt.addInfo(k, v)
        self.reporter.sendReport(evt, False)

    def _report_info_event(self, event):
        print("Found info event")
        print(dir(event))
        print(event)
        evt = Context.createEvent(int(event.timestamp / 1000))
        evt.addInfo('Label', 'info')
        for k, v in event.attributes.items():
            evt.addInfo(k, v)
        self.reporter.sendReport(evt, False)

    def _initialize_solarwinds_reporter(self):
        """Initialize liboboe."""
        log_level = os.environ.get('SOLARWINDS_DEBUG_LEVEL', 3)
        try:
            log_level = int(log_level)
        except ValueError:
            log_level = 3
        self.reporter = Reporter(
            hostname_alias='',
            log_level=log_level,
            log_file_path='',
            max_transactions=-1,
            max_flush_wait_time=-1,
            events_flush_interval=-1,
            max_request_size_bytes=-1,
            reporter='ssl',
            host=os.environ.get('SOLARWINDS_COLLECTOR', ''),
            service_key=os.environ.get('SOLARWINDS_SERVICE_KEY', ''),
            trusted_path='',
            buffer_size=-1,
            trace_metrics=-1,
            histogram_precision=-1,
            token_bucket_capacity=-1,
            token_bucket_rate=-1,
            file_single=0,
            ec2_metadata_timeout=1000,
            grpc_proxy='',
            stdout_clear_nonblocking=0,
            is_grpc_clean_hack_enabled=False,
            w3c_trace_format=1,
        )

    @staticmethod
    def _build_metadata(span_context):
        return Metadata.fromString(
            W3CTransformer.traceparent_from_context(span_context)
        )
