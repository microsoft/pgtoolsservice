# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.core import adapter
from ossdbtoolsservice.connection.core.owner_connection_info import (
    OwnerConnectionInfo,
)
from ossdbtoolsservice.connection.core.pooled_connection import PooledConnection
from ossdbtoolsservice.connection.core.server_connection import ServerConnection

# Add adapters to psycopg
adapter.addAdapters()

__all__ = [
    "ConnectionService",
    "OwnerConnectionInfo",
    "PooledConnection",
    "ServerConnection",
]
