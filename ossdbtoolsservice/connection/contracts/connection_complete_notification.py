# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import (
    ConnectionSummary,
    ServerInfo,
)
from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ConnectionCompleteParams(PGTSBaseModel):
    """Parameters to be sent back with a connection complete event"""

    owner_uri: str
    connection_id: str | None = None
    messages: str | None = None
    error_message: str | None = None
    error_number: int = 0
    server_info: ServerInfo | None = None
    connection_summary: ConnectionSummary | None = None

    @classmethod
    def create_error(
        cls,
        owner_uri: str,
        error_message: str,
    ) -> "ConnectionCompleteParams":
        """Create an error connection complete params"""
        return cls(
            owner_uri=owner_uri,
            messages=error_message,
            error_message=error_message,
        )


CONNECTION_COMPLETE_METHOD = "connection/complete"
OutgoingMessageRegistration.register_outgoing_message(ConnectionCompleteParams)
OutgoingMessageRegistration.register_outgoing_message(ServerInfo)
