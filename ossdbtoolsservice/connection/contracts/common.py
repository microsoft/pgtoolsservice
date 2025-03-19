# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import enum
import time
from typing import Any

from psycopg.conninfo import conninfo_to_dict, make_conninfo
from pydantic import field_validator

from ossdbtoolsservice.connection.core.constants import (
    PG_CONNECTION_OPTION_KEY_MAP,
    PG_CONNECTION_PARAM_KEYWORDS,
)
from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace.contracts import Configuration


class ConnectionSummary(PGTSBaseModel):
    """Provides high level information about a connection"""

    server_name: str
    database_name: str
    user_name: str


class ServerInfo(PGTSBaseModel):
    """Contract for information on the connected server"""

    server: str
    server_version: str
    is_cloud: bool

    @field_validator("server_version")
    @classmethod
    def validate_server_version(cls, v: str) -> str:
        """Validates the server version string."""
        split = v.split(".")
        if len(split) != 3 or not all(x.isdigit() for x in split):
            raise ValueError(f"Invalid server version: {v}")
        return v


class AzureToken(PGTSBaseModel):
    token: str
    expiry: int
    """Token and expiry time for Azure authentication.
    
    In Unix time format, the number of seconds elapsed since midnight,
    January 1, 1970 Universal Coordinated Time (UTC).
    """

    def is_azure_token_expired(self) -> bool:
        """Returns True if the token is expired or expiring within 30 seconds."""
        now = int(time.time())
        max_tolerance = 30

        return self.expiry <= (now + max_tolerance)


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
    def azure_account_id(self) -> str | None:
        return self._get_str_option("azureAccountId")

    @property
    def azure_tenant_id(self) -> str | None:
        return self._get_str_option("azureTenantId")

    @property
    def azure_token(self) -> AzureToken | None:
        token = self._get_str_option("azureAccountToken")
        expiry = self._get_int_option("azureTokenExpiry")
        if token and expiry:
            return AzureToken(token=token, expiry=expiry)
        return None

    @azure_token.setter
    def azure_token(self, value: AzureToken) -> None:
        self.options["azureAccountToken"] = value.token
        self.options["azureTokenExpiry"] = value.expiry

    @property
    def connect_timeout(self) -> int:
        """
        Returns the connect timeout in seconds.
        """
        try:
            connect_timeout = self._get_int_option("connectTimeout")
        except ValueError:
            return constants.DEFAULT_CONNECT_TIMEOUT
        return (
            connect_timeout
            if connect_timeout is not None
            else constants.DEFAULT_CONNECT_TIMEOUT
        )

    def get_connection_params(self, config: Configuration | None = None) -> dict[str, Any]:
        """
        Returns the connection parameters as a dictionary.
        This is used to pass the connection parameters to the driver.
        """
        connection_options = self.options.copy()
        if "azureAccountToken" in connection_options:
            connection_options["password"] = connection_options["azureAccountToken"]

        # Map the connection options to the correct keywords
        # for the psycopg driver
        # This will also remove any options that are not in the
        # PG_CONNECTION_PARAM_KEYWORDS list
        transformed_options = {}
        for option, value in connection_options.items():
            mapped_option = PG_CONNECTION_OPTION_KEY_MAP.get(option, option)
            if mapped_option in PG_CONNECTION_PARAM_KEYWORDS:
                transformed_options[mapped_option] = value

        # Flag to determine whether server is Azure Cosmos PG server
        is_cosmos = "host" in transformed_options and str(
            transformed_options["host"]
        ).endswith(".postgres.cosmos.azure.com")

        # Use the correct default DB depending on whether config is defined and
        # whether the server is an Azure Cosmos PG server
        default_database = (
            config.pgsql.default_database
            if config
            else constants.DEFAULT_DB[constants.PG_DEFAULT_DB]
        )
        if is_cosmos and config:
            default_database = config.pgsql.cosmos_default_database
        elif is_cosmos and not config:
            default_database = constants.DEFAULT_DB[constants.COSMOS_PG_DEFAULT_DB]

        # Use the default database if one was not provided
        if "dbname" not in transformed_options or not transformed_options["dbname"]:
            transformed_options["dbname"] = default_database

        # Use the default port number if one was not provided
        if "port" not in transformed_options or not transformed_options["port"]:
            transformed_options["port"] = constants.DEFAULT_PORT[constants.PG_PROVIDER_NAME]

        return transformed_options

    def validate_connection_params(self) -> None:
        """
        Validates the connection parameters.
        Raises an error if any of the required parameters are missing.
        """
        connection_params = self.get_connection_params()
        required_connection_params = [
            "host",
            "port",
            "user",
            "dbname",
        ]

        for param in required_connection_params:
            if param not in connection_params:
                raise ValueError(f"Missing required parameter: {param}")

        azure_required_params = [
            "azureAccountId",
            "azureTokenExpiry",
        ]
        if self.azure_token:
            for param in azure_required_params:
                if param not in self.options:
                    raise ValueError(f"Missing required parameter for Azure: {param}")

    def to_hash(self) -> int:
        """
        Returns hash of the connection details.
        """
        return hash(make_conninfo(**self.get_connection_params()))

    @classmethod
    def from_connection_string(cls, conn_str: str) -> "ConnectionDetails":
        """
        Creates a ConnectionDetails object from a connection string.
        """
        conn_info: dict[str, str | int] = {
            k: v for (k, v) in conninfo_to_dict(conn_str).items() if isinstance(v, (str, int))
        }
        return cls.from_data(opts=conn_info)

    @property
    def azure_subscription_id(self) -> str | None:
        return self._get_str_option("azureSubscriptionId")

    @property
    def azure_resource_group(self) -> str | None:
        return self._get_str_option("azureResourceGroup")

    @property
    def copilot_access_mode(self) -> str | None:
        return self._get_str_option("copilotAccessMode")

    @property
    def is_azure_pg(self) -> bool:
        host = self.server_name
        if not host:
            return False
        return host.endswith(".postgres.database.azure.com")


class ConnectionType(str, enum.Enum):
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

    def __str__(self) -> str:
        return str(self.value)
