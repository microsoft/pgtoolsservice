# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType  # noqa
from pgsqltoolsservice.serialization import Serializable


class ConnectRequestParams(Serializable):

    @classmethod
    def get_child_serializable_types(cls):
        return {'connection': ConnectionDetails}

    def __init__(self, connection=None, owner_uri=None, connection_type=ConnectionType.DEFAULT):
        self.connection: ConnectionDetails = connection
        self.owner_uri: str = owner_uri
        self.type: ConnectionType = connection_type


CONNECT_REQUEST = IncomingMessageConfiguration('connection/connect', ConnectRequestParams)
