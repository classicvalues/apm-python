# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import configurator

class TestConfiguratorAddAllInstrumentedFrameworkVersions:
    def test_add_all_instr_versions_skip_disabled_instrumentors(
        self,
        mocker,
    ):
        # Save any DISABLED env var for later
        old_disabled = os.environ.get("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", None)
        if old_disabled:
            del os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"]

        mocker.patch.dict(
            os.environ,
            {
                "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS": "foo-bar-module"
            }
        )

        # Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": "foo-bar-module",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.foo-bar-module.Version" not in test_versions

        # Restore old DISABLED
        if old_disabled:
            os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = old_disabled

    def test_add_all_instr_versions_skip_dependency_conflict(
        self,
        mocker,
    ):
        # Mock conflicts - not None
        mocker.patch(
            "solarwinds_apm.configurator.get_dist_dependency_conflicts",
            return_value="not-none"
        )

        # Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": "foo-bar-module",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_skip_conflict_check_exception(
        self,
        mocker,
    ):
        # Mock conflicts - exception
        mocker.patch(
            "solarwinds_apm.configurator.get_dist_dependency_conflicts",
            side_effect=Exception("mock conflict")
        )

        # Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": "foo-bar-module",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_skip_module_lookup_exception(
        self,
        mocker,
    ):
        # Mock importlib - error
        mock_importlib_import_module = mocker.Mock(
            side_effect=AttributeError("mock error")
        )
        mock_importlib = mocker.patch(
            "solarwinds_apm.configurator.importlib"
        )
        mock_importlib.configure_mock(
            **{
                "import_module": mock_importlib_import_module
            }
        )

        # Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": "foo-bar-module",
                "dist": "foo",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # Mock conflicts - none
        mocker.patch(
            "solarwinds_apm.configurator.get_dist_dependency_conflicts",
            return_value=None,
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        assert "Python.foo-bar-module.Version" not in test_versions

    def test_add_all_instr_versions_aiohttp_client(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_grpc(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_system_metrics(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_tortoiseorm(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_mysql(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_elasticsearch(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_pyramid(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_sqlite3(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_tornado(
        self,
        mocker,
    ):
        pass

    def test_add_all_instr_versions_urllib(
        self,
        mocker,
    ):
        # Mock importlib
        mock_importlib_import_module = mocker.Mock()
        mock_importlib = mocker.patch(
            "solarwinds_apm.configurator.importlib"
        )
        mock_importlib.configure_mock(
            **{
                "import_module": mock_importlib_import_module
            }
        )

        # Mock sys module
        mock_sys_module = mocker.Mock()
        mock_sys_module.configure_mock(
            **{
                "__version__": "foo-version"
            }
        )
        mock_sys = mocker.patch(
            "solarwinds_apm.configurator.sys"
        )
        mock_sys.configure_mock(
            **{
                "modules": {
                    "urllib.request": mock_sys_module
                }
            }
        )

        # Mock entry point
        mock_instrumentor_entry_point = mocker.Mock()
        mock_instrumentor_entry_point.configure_mock(
            **{
                "name": "urllib",
                "dist": "foo",
            }
        )
        mock_points = iter([mock_instrumentor_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        # Mock conflicts - none
        mocker.patch(
            "solarwinds_apm.configurator.get_dist_dependency_conflicts",
            return_value=None,
        )

        # Test!
        test_versions = configurator.SolarWindsConfigurator()._add_all_instrumented_python_framework_versions({"foo": "bar"})
        assert test_versions["foo"] == "bar"
        # TODO: should be capitalized Urllib
        assert "Python.urllib.Version" in test_versions
        assert test_versions["Python.urllib.Version"] == "foo-version"

    def test_add_all_instr_versions_urllib3_nonspecial_case(
        self,
        mocker,
    ):
        pass
