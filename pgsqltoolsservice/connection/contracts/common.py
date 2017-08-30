# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum

from pgsqltoolsservice.serialization import Serializable


class ConnectionSummary:
    """Provides high level information about a connection"""

    def __init__(self, server_name: str, database_name: str, user_name: str):
        self.server_name: str = server_name
        self.database_name: str = database_name
        self.user_name: str = user_name


class ConnectionDetails(Serializable):
    """
    Details about the connection on top of a basic connection summary. Used as part of the incoming
    connection request
    """
    @classmethod
    def from_data(cls, server_name: str, database_name: str, user_name: str, opts: dict):
        obj = cls()
        obj.user_name = user_name
        obj.database_name = database_name
        obj.server_name = server_name
        obj.options = opts
        return obj

    def __init__(self):
        self.options: dict = None
        self.server_name: str = None
        self.database_name: str = None
        self.user_name: str = None


class ConnectionType(enum.Enum):
    """
    String constants that represent connection types.

    Default: Connection used by the editor. Opened by the editor upon the initial connection.
    Query: Connection used for executing queries. Opened when the first query is executed.
    """
    DEFAULT = 'Default'
    QUERY = 'Query'
    EDIT = 'Edit'
    QUERY_CANCEL = 'QueryCancel'
    OBJECT_EXLPORER = 'ObjectExplorer'
    INTELLISENSE = 'Intellisense'
