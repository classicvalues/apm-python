# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to configure OpenTelemetry to work with SolarWinds backend"""

import logging
from os import environ

from opentelemetry.environment_variables import (
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.logging.environment_variables import (
    OTEL_PYTHON_LOG_FORMAT,
)
from pkg_resources import EntryPoint

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_METRICS_EXPORTER_LAMBDA,
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
    INTL_SWO_DEFAULT_TRACES_EXPORTER_LAMBDA,
)

logger = logging.getLogger(__name__)


class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    def _configure(self, **kwargs):
        """Configure default OTel exporter and propagators"""
        is_lambda = SolarWindsApmConfig.calculate_is_lambda()
        if is_lambda:
            environ.setdefault(
                OTEL_METRICS_EXPORTER, INTL_SWO_DEFAULT_METRICS_EXPORTER_LAMBDA
            )
            environ.setdefault(
                OTEL_TRACES_EXPORTER, INTL_SWO_DEFAULT_TRACES_EXPORTER_LAMBDA
            )
        else:
            # If experimental flag set, users need to specify OTEL_METRICS_EXPORTER
            # or none will be loaded.
            environ.setdefault(
                OTEL_TRACES_EXPORTER, INTL_SWO_DEFAULT_TRACES_EXPORTER
            )

        environ.setdefault(
            OTEL_PROPAGATORS, ",".join(INTL_SWO_DEFAULT_PROPAGATORS)
        )
        environ.setdefault(
            OTEL_PYTHON_LOG_FORMAT,
            "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s trace_flags=%(otelTraceSampled)02d resource.service.name=%(otelServiceName)s] - %(message)s",
        )

    def load_instrumentor(self, entry_point: EntryPoint, **kwargs):
        """Takes a collection of instrumentation entry points
        and activates them by instantiating and calling instrument()
        on each one. This is a method override to pass additional
        arguments to each entry point.
        """
        # Set enable for sqlcommenter. Assumes kwargs ignored if not
        # implemented for current instrumentation library
        if self.enable_commenter():
            # instrumentation for Flask ORM, sqlalchemy, psycopg2
            kwargs["enable_commenter"] = True
            # instrumentation for Django ORM
            kwargs["is_sql_commentor_enabled"] = True

            # Assumes can be empty and any KVs not used
            # by current library are ignored
            # Note: Django ORM accepts options in settings.py
            # https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/django/django.html
            kwargs["commenter_options"] = self.detect_commenter_options()
        instrumentor: BaseInstrumentor = entry_point.load()
        instrumentor().instrument(**kwargs)

    def enable_commenter(self) -> bool:
        """Enable sqlcommenter feature, if implemented"""
        # TODO: Update if changed in OTel spec:
        # https://github.com/open-telemetry/opentelemetry-specification/issues/3560
        enable_commenter = environ.get("OTEL_SQLCOMMENTER_ENABLED", "")
        if enable_commenter.lower() == "true":
            return True
        return False

    def detect_commenter_options(self):
        """Returns commenter options dict parsed from environment, if any"""
        commenter_opts = {}
        commenter_opts_env = environ.get("OTEL_SQLCOMMENTER_OPTIONS")
        if commenter_opts_env:
            for opt_item in commenter_opts_env.split(","):
                opt_k = ""
                opt_v = ""
                try:
                    opt_k, opt_v = opt_item.split("=", maxsplit=1)
                except ValueError as exc:
                    logger.warning(
                        "Invalid key-value pair for sqlcommenter option %s: %s",
                        opt_item,
                        exc,
                    )
                opt_v_bool = SolarWindsApmConfig.convert_to_bool(opt_v.strip())
                if opt_v_bool is not None:
                    commenter_opts[opt_k.strip()] = opt_v_bool

        return commenter_opts
