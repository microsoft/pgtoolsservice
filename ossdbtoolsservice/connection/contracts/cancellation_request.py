# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class CancelConnectParams(Serializable):
    """Parameters for the cancel connect request"""

    owner_uri: str | None

    def __init__(
        self,
        owner_uri: str | None = None,
        connection_type: ConnectionType = ConnectionType.DEFAULT,
    ) -> None:
        self.owner_uri = owner_uri
        self.type: ConnectionType = connection_type


CANCEL_CONNECT_REQUEST = IncomingMessageConfiguration(
    "connection/cancelconnect", CancelConnectParams
)
