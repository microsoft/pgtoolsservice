# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.connection.contracts.common import ConnectionSummary, ConnectionType     # noqa


class ConnectionCompleteParams:
    """Parameters to be sent back with a connection complete event"""

    def __init__(self):
        self.owner_uri: str = None
        self.connection_id: str = None
        self.messages: str = None
        self.error_message: str = None
        self.error_number: int = 0
        self.server_info: ServerInfo = None
        self.connection_summary: ConnectionSummary = None
        self.type: ConnectionType = ConnectionType.DEFAULT


class ServerInfo(object):
    """Contract for information on the connected PostgreSQL server"""

    def __init__(self, server_version, is_cloud):
        self.server_version: str = server_version
        self.is_cloud: bool = is_cloud


CONNECTION_COMPLETE_METHOD = 'connection/complete'
