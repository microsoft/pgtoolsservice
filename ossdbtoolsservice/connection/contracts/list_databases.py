# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the connection/listdatabases method"""

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class ListDatabasesParams(Serializable):
    """Parameters for the connection/listdatabases request"""

    owner_uri: str
    include_details: bool

    def __init__(self):
        self.owner_uri: str = None
        self.include_details: bool = None


class ListDatabasesResponse:
    """Response for the connection/listdatabases request"""

    database_names: list[str]

    def __init__(self, database_names):
        self.database_names: list[str] = database_names


LIST_DATABASES_REQUEST = IncomingMessageConfiguration(
    "connection/listdatabases", ListDatabasesParams
)
OutgoingMessageRegistration.register_outgoing_message(ListDatabasesResponse)
