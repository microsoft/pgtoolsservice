# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Dict  # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class GetDatabaseInfoParameters(Serializable):
    """Contract for the parameters to admin/getdatabaseinfo requests"""

    def __init__(self):
        self.options: dict = None
        self.owner_uri: str = None


class DatabaseInfo:
    """Contract for database information"""
    OWNER = 'owner'

    def __init__(self, options: Dict[str, Any]) -> None:
        self.options: Dict[str, Any] = options


class GetDatabaseInfoResponse:
    """Contract for the response to admin/getdatabaseinfo requests"""

    def __init__(self, database_info: DatabaseInfo) -> None:
        self.database_info: DatabaseInfo = database_info


GET_DATABASE_INFO_REQUEST = IncomingMessageConfiguration('admin/getdatabaseinfo', GetDatabaseInfoParameters)
