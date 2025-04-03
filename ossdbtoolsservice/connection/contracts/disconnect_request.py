# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class DisconnectRequestParams(Serializable):
    owner_uri: str | None
    type: ConnectionType | None

    def __init__(
        self, owner_uri: str | None = None, type: ConnectionType | None = None
    ) -> None:
        self.owner_uri = owner_uri
        self.type = type


DISCONNECT_REQUEST = IncomingMessageConfiguration(
    "connection/disconnect", DisconnectRequestParams
)
