# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from opentelemetry.environment_variables import (
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)

from solarwinds_apm.distro import SolarWindsDistro

class TestDistro:
    def test_configure_no_env(self, mocker):
        mocker.patch.dict(os.environ, {})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
        assert not os.environ.get(OTEL_METRICS_EXPORTER)

    def test_configure_env_exporter(self, mocker):
        mocker.patch.dict(
            os.environ, 
                {
                    "OTEL_TRACES_EXPORTER": "foobar",
                    "OTEL_METRICS_EXPORTER": "baz"
                }
        )
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"

    def test_configure_no_env_lambda(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "foo",
                "LAMBDA_TASK_ROOT": "bar"
            },
            clear=True
        )
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "otlp_proto_http"
        assert os.environ[OTEL_METRICS_EXPORTER] == "otlp_proto_http"

    def test_configure_env_exporter_lambda(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "foo",
                "LAMBDA_TASK_ROOT": "bar",
                "OTEL_TRACES_EXPORTER": "foobar",
                "OTEL_METRICS_EXPORTER": "baz"
            }
        )
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"
        assert os.environ[OTEL_METRICS_EXPORTER] == "baz"

    def test_configure_env_propagators(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,solarwinds_propagator,foobar"})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,solarwinds_propagator,foobar"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"

    def test_load_instrumentor_no_commenting(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "load": mock_load
            }
        )
        SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(**{"foo": "bar"})  

    def test_load_instrumentor_enable_commenting(self, mocker):
        mock_instrument = mocker.Mock()
        mock_instrumentor = mocker.Mock()
        mock_instrumentor.configure_mock(
            return_value=mocker.Mock(
                **{
                    "instrument": mock_instrument
                }
            )
        )
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_instrumentor)
        mock_entry_point = mocker.Mock()
        mock_entry_point.configure_mock(
            **{
                "load": mock_load
            }
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.enable_commenter",
            return_value=True
        )
        mocker.patch(
            "solarwinds_apm.distro.SolarWindsDistro.detect_commenter_options",
            return_value="foo-options"
        )
        SolarWindsDistro().load_instrumentor(mock_entry_point, **{"foo": "bar"})
        mock_instrument.assert_called_once_with(
            commenter_options="foo-options",
            enable_commenter=True,
            foo="bar",
            is_sql_commentor_enabled=True,
        )

    def test_enable_commenter_none(self, mocker):
        mocker.patch.dict(os.environ, {})
        assert SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_non_bool_value(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "foo"})
        assert SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_false(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "false"})
        assert SolarWindsDistro().enable_commenter() == False
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "False"})
        assert SolarWindsDistro().enable_commenter() == False
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "faLsE"})
        assert SolarWindsDistro().enable_commenter() == False

    def test_enable_commenter_true(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "true"})
        assert SolarWindsDistro().enable_commenter() == True
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "True"})
        assert SolarWindsDistro().enable_commenter() == True
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_ENABLED": "tRuE"})
        assert SolarWindsDistro().enable_commenter() == True

    def test_detect_commenter_options_not_set(self, mocker):
        mocker.patch.dict(os.environ, {})
        result = SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_invalid_kv_ignored(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "invalid-kv,foo=bar"})
        result = SolarWindsDistro().detect_commenter_options()
        assert result == {}

    def test_detect_commenter_options_valid_kvs(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "foo=true,bar=FaLSe"})
        result = SolarWindsDistro().detect_commenter_options()
        assert result == {
            "foo": True,
            "bar": False,
        }

    def test_detect_commenter_options_strip_whitespace_ok(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_SQLCOMMENTER_OPTIONS": "   foo   =   tRUe   , bar = falsE "
            }
        )
        result = SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False

    def test_detect_commenter_options_strip_mix(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_SQLCOMMENTER_OPTIONS": "invalid-kv,   foo=TrUe   ,bar  =  faLSE,   baz=qux  "})
        result = SolarWindsDistro().detect_commenter_options()
        assert result.get("foo") == True
        assert result.get("bar") == False
        assert result.get("baz") is None
