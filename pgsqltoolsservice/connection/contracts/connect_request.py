# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType  # noqa
import pgsqltoolsservice.utils as utils


class ConnectRequestParams:
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.deserialize_from_dict(cls, dictionary,
                                           connection=ConnectionDetails)

    def __init__(self):
        self.connection: ConnectionDetails = None
        self.owner_uri: str = None
        self.type: ConnectionType = None


CONNECT_REQUEST = IncomingMessageConfiguration('connection/connect', ConnectRequestParams)
