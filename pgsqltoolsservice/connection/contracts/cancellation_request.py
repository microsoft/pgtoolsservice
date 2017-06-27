# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.connection.contracts.common import ConnectionType
from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class CancelConnectParams:
    """Parameters for the cancel connect request"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        """Method to create an instance of the class from a dictionary (for deserialization)"""
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self, owner_uri: str = None, connection_type: ConnectionType = ConnectionType.DEFAULT):
        self.owner_uri: str = owner_uri
        self.type: ConnectionType = connection_type


CANCEL_CONNECT_REQUEST = IncomingMessageConfiguration('connection/cancelconnect', CancelConnectParams)
