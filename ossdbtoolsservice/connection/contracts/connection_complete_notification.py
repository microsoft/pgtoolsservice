# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import ConnectionSummary, ConnectionType  # noqa
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ServerInfo:
    """Contract for information on the connected server"""

    server: str
    server_version: str
    is_cloud: bool

    def __init__(
        self, server: str, server_version: tuple[int, int, int], is_cloud: bool
    ) -> None:
        self.server = server
        self.server_version = (
            str(server_version[0])
            + "."
            + str(server_version[1])
            + "."
            + str(server_version[2])
        )
        self.is_cloud: bool = is_cloud


class ConnectionCompleteParams:
    """Parameters to be sent back with a connection complete event"""

    owner_uri: str | None
    connection_id: str | None
    messages: str | None
    error_message: str | None
    error_number: int | None
    server_info: ServerInfo | None
    connection_summary: ConnectionSummary | None
    type: ConnectionType

    def __init__(self) -> None:
        self.owner_uri = None
        self.connection_id = None
        self.messages = None
        self.error_message = None
        self.error_number = 0
        self.server_info = None
        self.connection_summary = None
        self.type: ConnectionType = ConnectionType.DEFAULT


CONNECTION_COMPLETE_METHOD = "connection/complete"
OutgoingMessageRegistration.register_outgoing_message(ConnectionCompleteParams)
OutgoingMessageRegistration.register_outgoing_message(ServerInfo)
