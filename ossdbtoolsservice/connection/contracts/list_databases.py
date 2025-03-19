# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the connection/listdatabases method"""

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class ListDatabasesParams(Serializable):
    """Parameters for the connection/listdatabases request"""

    owner_uri: str | None
    include_details: bool | None

    def __init__(
        self, owner_uri: str | None = None, include_details: bool | None = None
    ) -> None:
        self.owner_uri = owner_uri
        self.include_details = include_details


class ListDatabasesResponse(PGTSBaseModel):
    """Response for the connection/listdatabases request"""

    database_names: list[str]


LIST_DATABASES_REQUEST = IncomingMessageConfiguration(
    "connection/listdatabases", ListDatabasesParams
)
OutgoingMessageRegistration.register_outgoing_message(ListDatabasesResponse)
