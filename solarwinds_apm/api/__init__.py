# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
from typing import Any

from opentelemetry.trace import get_current_span, get_tracer_provider

from solarwinds_apm.apm_oboe_codes import OboeReadyCode
from solarwinds_apm.extension.oboe import Context
from solarwinds_apm.inbound_metrics_processor import SolarWindsInboundMetricsSpanProcessor

logger = logging.getLogger(__name__)


def set_transaction_name(name: str) -> None:
    # Assumes TracerProvider's active span processor is SynchronousMultiSpanProcessor
    # or ConcurrentMultiSpanProcessor
    span_processors = get_tracer_provider()._active_span_processor._span_processors
    inbound_processor = None
    for spr in span_processors:
        if type(spr) == SolarWindsInboundMetricsSpanProcessor:
            inbound_processor = spr

    if not inbound_processor:
        logger.error("Could not find configured InboundMetricsSpanProcessor.")
        return

    current_span = get_current_span()
    trace_id = current_span.get_span_context().trace_id
    logger.debug("TODO: Implement me!")
    # inbound_processor._apm_txname_customizer[trace_id] = name
    # logger.debug("Cached custom transaction name as %s", name)


def solarwinds_ready(
    wait_milliseconds: int = 3000,
    integer_response: bool = False,
) -> Any:
    """
    Wait for SolarWinds to be ready to send traces.

    This may be useful in short lived background processes when it is important to capture
    information during the whole time the process is running. Usually SolarWinds doesn't block an
    application while it is starting up.

    :param wait_milliseconds:int default 3000, the maximum time to wait in milliseconds
    :param integer_response:bool default False to return boolean value, otherwise True to
    return integer for detailed information

    :return:
    if integer_response:int code 1 for ready; 0,2,3,4,5 for not ready
    else:bool True for ready, False not ready,

    :Example:
     from solarwinds_apm.api import solarwinds_ready
     if not solarwinds_ready(wait_milliseconds=10000, integer_response=True):
        Logger.info("SolarWinds not ready after 10 seconds, no metrics will be sent")
    """
    rc = Context.isReady(wait_milliseconds)
    if not isinstance(rc, int) or rc not in OboeReadyCode.code_values():
        logger.warning("Unrecognized return code: %s", rc)
        return (
            OboeReadyCode.OBOE_SERVER_RESPONSE_UNKNOWN
            if integer_response
            else False
        )
    if rc != OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]:
        logger.warning(OboeReadyCode.code_values()[rc])

    return (
        rc
        if integer_response
        else rc == OboeReadyCode.OBOE_SERVER_RESPONSE_OK[0]
    )
