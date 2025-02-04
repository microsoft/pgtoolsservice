# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.contracts.common import ConnectionType
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class BuildConnectionInfoParams(Serializable):
    """Parameters for Serializing Connection String request"""
    owner_uri: str
    type: ConnectionType

    def __init__(self, owner_uri: str = None, connection_type: ConnectionType = ConnectionType.DEFAULT):
        self.owner_uri: str = owner_uri
        self.type: ConnectionType = connection_type


BUILD_CONNECTION_INFO_REQUEST = IncomingMessageConfiguration('connection/buildconnectioninfo', BuildConnectionInfoParams)
