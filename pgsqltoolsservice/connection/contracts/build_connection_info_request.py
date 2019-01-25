# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.connection.contracts.common import ConnectionType
from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class BuildConnectionInfoParams(Serializable):
    """Parameters for Serializing Connection String request"""

    def __init__(self, owner_uri: str = None, connection_type: ConnectionType = ConnectionType.DEFAULT):
        self.owner_uri: str = owner_uri
        self.type: ConnectionType = connection_type


BUILD_CONNECTION_INFO_REQUEST = IncomingMessageConfiguration('connection/buildconnectioninfo', BuildConnectionInfoParams)
