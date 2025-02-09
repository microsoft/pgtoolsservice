# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Dict  # noqa

from ossdbtoolsservice.hosting.message_configuration import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)
from ossdbtoolsservice.serialization import Serializable


class GetDatabaseInfoParameters(Serializable):
    """Contract for the parameters to admin/getdatabaseinfo requests"""

    options: dict
    owner_uri: str

    def __init__(self):
        self.options: dict = None
        self.owner_uri: str = None


class DatabaseInfo:
    """Contract for database information"""

    OWNER: str = "owner"
    DBNAME: str = "dbname"
    SIZE: str = "size"

    def __init__(self, options: Dict[str, Any]) -> None:
        self.options: Dict[str, Any] = options


class GetDatabaseInfoResponse:
    """Contract for the response to admin/getdatabaseinfo requests"""

    database_info: DatabaseInfo

    def __init__(self, database_info: DatabaseInfo) -> None:
        self.database_info: DatabaseInfo = database_info


GET_DATABASE_INFO_REQUEST = IncomingMessageConfiguration(
    "admin/getdatabaseinfo", GetDatabaseInfoParameters
)
OutgoingMessageRegistration.register_outgoing_message(GetDatabaseInfoResponse)
OutgoingMessageRegistration.register_outgoing_message(DatabaseInfo)
