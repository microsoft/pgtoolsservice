# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ostoolsservice.hosting import IncomingMessageConfiguration
from ostoolsservice.serialization import Serializable


class GetConnectionStringParams(Serializable):
    """Parameters for Getting Connection String request"""

    def __init__(self, owner_uri: str = None):
        self.owner_uri: str = owner_uri


GET_CONNECTION_STRING_REQUEST = IncomingMessageConfiguration('connection/getconnectionstring', GetConnectionStringParams)
