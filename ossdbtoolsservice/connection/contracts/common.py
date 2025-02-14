# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum

from ossdbtoolsservice.serialization import Serializable


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

    options: dict

    @classmethod
    def from_data(cls, opts: dict):
        obj = cls()
        obj.options = opts
        return obj

    def __init__(self):
        self.options: dict = {}

    @property
    def server_name(self) -> str:
        if not self.options:
            return None
        return self.options.get("host")

    @server_name.setter
    def server_name(self, value):
        self.options["host"] = value

    @property
    def database_name(self) -> str:
        if not self.options:
            return None
        return self.options.get("dbname")

    @database_name.setter
    def database_name(self, value):
        self.options["dbname"] = value

    @property
    def user_name(self) -> str:
        if not self.options:
            return None
        return self.options.get("user")

    @user_name.setter
    def user_name(self, value):
        self.options["user"] = value

    @property
    def port(self) -> int:
        if not self.options:
            return None
        val = self.options.get("port")
        if val:
            return int(val) or None

    @port.setter
    def port(self, value):
        self.options["port"] = value


class ConnectionType(enum.Enum):
    """
    String constants that represent connection types.

    Default: Connection used by the editor. Opened by the editor upon the initial connection.
    Query: Connection used for executing queries. Opened when the first query is executed.
    """

    DEFAULT = "Default"
    QUERY = "Query"
    EDIT = "Edit"
    QUERY_CANCEL = "QueryCancel"
    OBJECT_EXLPORER = "ObjectExplorer"
    INTELLISENSE = "Intellisense"
