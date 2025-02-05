# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import ConnectionSummary, ConnectionType     # noqa
from ossdbtoolsservice.hosting import OutgoingMessageRegistration


class ServerInfo(object):
    """Contract for information on the connected server"""
    server: str
    server_version: str
    is_cloud: bool

    def __init__(self, server: str, server_version, is_cloud):
        self.server = server
        self.server_version = str(server_version[0]) + "." + str(server_version[1]) + "." + str(server_version[2])
        self.is_cloud: bool = is_cloud


class ConnectionCompleteParams:
    """Parameters to be sent back with a connection complete event"""
    owner_uri: str
    connection_id: str
    messages: str
    error_message: str
    error_number: int
    server_info: ServerInfo
    connection_summary: ConnectionSummary
    type: ConnectionType

    def __init__(self):
        self.owner_uri: str = None
        self.connection_id: str = None
        self.messages: str = None
        self.error_message: str = None
        self.error_number: int = 0
        self.server_info: ServerInfo = None
        self.connection_summary: ConnectionSummary = None
        self.type: ConnectionType = ConnectionType.DEFAULT


CONNECTION_COMPLETE_METHOD = 'connection/complete'
OutgoingMessageRegistration.register_outgoing_message(ConnectionCompleteParams)
OutgoingMessageRegistration.register_outgoing_message(ServerInfo)
