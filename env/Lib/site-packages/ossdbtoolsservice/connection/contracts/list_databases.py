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

    owner_uri: str | None
    include_details: bool | None

    def __init__(self) -> None:
        self.owner_uri = None
        self.include_details = None


class ListDatabasesResponse:
    """Response for the connection/listdatabases request"""

    database_names: list[str]

    def __init__(self, database_names: list[str]) -> None:
        self.database_names = database_names


LIST_DATABASES_REQUEST = IncomingMessageConfiguration(
    "connection/listdatabases", ListDatabasesParams
)
OutgoingMessageRegistration.register_outgoing_message(ListDatabasesResponse)
