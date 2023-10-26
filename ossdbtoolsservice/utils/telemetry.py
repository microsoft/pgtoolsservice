# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.serialization import Serializable


class TelemetryParams(Serializable):
    """Parameters to be sent back with a telemetry event"""

    def __init__(self, eventName: str, properties: dict(), measures: dict() = None):
        self.params = {
            'eventName': eventName,
            'properties': properties,
            'measures': measures
        }


def send_error_telemetry_notification(request_context, view: str, name: str, errorCode):
    if request_context is not None:
        request_context.send_notification(
            method=TELEMETRY_NOTIFICATION,
            params=TelemetryParams(
                TELEMETRY_ERROR_EVENT,
                {
                    'view': view,
                    'name': name,
                    'errorCode': str(errorCode)
                }
            )
        )


# Method name listened by client
TELEMETRY_NOTIFICATION = "telemetry/event"

# Telemetry Event Name for Errors
TELEMETRY_ERROR_EVENT = "telemetry/event/error"
