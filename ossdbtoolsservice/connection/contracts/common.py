# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum

from ossdbtoolsservice.serialization import Serializable


class ConnectionSummary:
    """Provides high level information about a connection"""

    def __init__(self, server_name: str, database_name: str, user_name: str) -> None:
        self.server_name: str = server_name
        self.database_name: str = database_name
        self.user_name: str = user_name


class ConnectionDetails(Serializable):
    """
    Details about the connection on top of a basic connection summary.
    Used as part of the incoming connection request
    """

    options: dict[str, str | int]

    @classmethod
    def from_data(cls, opts: dict[str, str | int]) -> "ConnectionDetails":
        obj = cls(opts)
        return obj

    def __init__(self, options: dict[str, str | int] | None = None) -> None:
        self.options: dict[str, str | int] = {} if options is None else options

    def _get_str_option(self, key: str) -> str | None:
        if not self.options:
            return None
        v = self.options.get(key)
        if v is None:
            return None
        return str(v)

    def _get_int_option(self, key: str) -> int | None:
        if not self.options:
            return None
        v = self.options.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except ValueError as e:
            raise ValueError(f"Invalid value for {key}: {v}. Requires int.") from e

    @property
    def server_name(self) -> str | None:
        return self._get_str_option("host")

    @server_name.setter
    def server_name(self, value: str) -> None:
        self.options["host"] = value

    @property
    def database_name(self) -> str | None:
        return self._get_str_option("dbname")

    @database_name.setter
    def database_name(self, value: str) -> None:
        self.options["dbname"] = value

    @property
    def user_name(self) -> str | None:
        return self._get_str_option("user")

    @user_name.setter
    def user_name(self, value: str) -> None:
        self.options["user"] = value

    @property
    def port(self) -> int | None:
        return self._get_int_option("port")

    @port.setter
    def port(self, value: int) -> None:
        self.options["port"] = value

    @property
    def password(self) -> str | None:
        return self._get_str_option("password")

    @password.setter
    def password(self, value: str) -> None:
        self.options["password"] = value

    @property
    def azure_account_token(self) -> str | None:
        return self._get_str_option("azureAccountToken")

    @azure_account_token.setter
    def azure_account_token(self, value: str) -> None:
        self.options["azureAccountToken"] = value

    @property
    def azure_subscription_id(self) -> str | None:
        return self._get_str_option("azureSubscriptionId")

    @property
    def azure_resource_group(self) -> str | None:
        return self._get_str_option("azureResourceGroup")


    @property
    def is_azure_pg(self) -> bool:
        host = self.server_name
        if not host:
            return False
        return host.endswith(".postgres.database.azure.com")


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
    OBJECT_EXLPORER = "ObjectExplorer"  # TODO: Fix typo
    INTELLISENSE = "Intellisense"
