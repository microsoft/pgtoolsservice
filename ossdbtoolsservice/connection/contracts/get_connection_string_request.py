# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class GetConnectionStringParams(Serializable):
    """Parameters for Getting Connection String request"""

    owner_uri: str | None

    def __init__(self, owner_uri: str | None = None) -> None:
        self.owner_uri = owner_uri


GET_CONNECTION_STRING_REQUEST = IncomingMessageConfiguration(
    "connection/getconnectionstring", GetConnectionStringParams
)
