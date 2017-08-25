# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds contracts for the connection/listdatabases method"""

from typing import List  # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class ListDatabasesParams(Serializable):
    """Parameters for the connection/listdatabases request"""
    def __init__(self):
        self.owner_uri: str = None


class ListDatabasesResponse:
    """Response for the connection/listdatabases request"""

    def __init__(self, database_names):
        self.database_names: List[str] = database_names


LIST_DATABASES_REQUEST = IncomingMessageConfiguration('connection/listdatabases', ListDatabasesParams)
