# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

def get_metrics_mocks(mocker):
    mock_meter_provider = mocker.patch(
        "solarwinds_apm.configurator.MeterProvider",
    )

    mock_set_meter_provider = mocker.Mock(
        return_value=mock_meter_provider
    )

    mock_metrics = mocker.patch(
        "solarwinds_apm.configurator.metrics",
    )
    mock_metrics.configure_mock(
        **{
            "set_meter_provider": mock_set_meter_provider
        }
    )
    return mock_metrics, mock_set_meter_provider, mock_meter_provider