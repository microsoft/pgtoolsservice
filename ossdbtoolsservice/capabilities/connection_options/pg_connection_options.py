# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.capabilities.contracts import (
    CategoryValue,
    ConnectionOption,
    ConnectionProviderOptions,
    DMPServerCapabilities,
)
from ossdbtoolsservice.disaster_recovery.contracts import BACKUP_OPTIONS, RESTORE_OPTIONS
from ossdbtoolsservice.query_execution.contracts import SERIALIZATION_OPTIONS
from ossdbtoolsservice.utils import constants

pg_conn_provider_opts = ConnectionProviderOptions(
    [
        ConnectionOption(
            name="host",
            display_name="Server name",
            description="Name of the PostgreSQL instance",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            special_value_type=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
            is_identity=True,
            is_required=True,
            group_name="Source",
        ),
        ConnectionOption(
            name="dbname",
            display_name="Database name",
            description="The name of the initial catalog or database in the data source",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            special_value_type=ConnectionOption.SPECIAL_VALUE_DATABASE_NAME,
            is_identity=True,
            is_required=False,
            group_name="Source",
            default_value=constants.DEFAULT_DB[constants.PG_DEFAULT_DB],
        ),
        ConnectionOption(
            name="user",
            display_name="User name",
            description="Indicates the user ID to be used when connecting to the data source",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            special_value_type=ConnectionOption.SPECIAL_VALUE_USER_NAME,
            is_identity=True,
            is_required=True,
            group_name="Security",
        ),
        ConnectionOption(
            name="password",
            display_name="Password",
            description=(
                "Indicates the password to be used when connecting to the data source"
            ),
            value_type=ConnectionOption.VALUE_TYPE_PASSWORD,
            special_value_type=ConnectionOption.SPECIAL_VALUE_PASSWORD_NAME,
            is_identity=True,
            is_required=True,
            group_name="Security",
        ),
        ConnectionOption(
            name="authenticationType",
            display_name="Authentication Type",
            description="Specifies the method of authenticating with PostgreSQL Server",
            value_type=ConnectionOption.VALUE_TYPE_CATEGORY,
            special_value_type=ConnectionOption.SPECIAL_VALUE_AUTH_TYPE,
            is_identity=True,
            is_required=True,
            category_values=[
                CategoryValue("Password", "SqlLogin"),
                CategoryValue("Entra Auth", "AzureMFA"),
            ],
            group_name="Security",
        ),
        ConnectionOption(
            name="azureAccountToken",
            display_name="Access Token",
            description="Indicates an Active Directory access token "
            "to be used when connecting to the data source",
            value_type=ConnectionOption.VALUE_TYPE_ACCESS_TOKEN,
            special_value_type=ConnectionOption.SPECIAL_VALUE_ACCESS_TOKEN_NAME,
            is_identity=True,
            is_required=False,
            group_name="Security",
        ),
        ConnectionOption(
            name="hostaddr",
            display_name="Host IP address",
            description="IP address of the server",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            is_identity=True,
            group_name="Server",
        ),
        ConnectionOption(
            name="port",
            display_name="Port",
            description="Port number for the server",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            is_identity=True,
            group_name="Server",
        ),
        ConnectionOption(
            name="connectTimeout",
            display_name="Connect timeout",
            description="Seconds to wait before timing out when connecting",
            value_type=ConnectionOption.VALUE_TYPE_NUMBER,
            group_name="Client",
            default_value="15",
        ),
        ConnectionOption(
            name="clientEncoding",
            display_name="Client encoding",
            description="The client encoding for the connection",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="Client",
            default_value="utf8",
        ),
        ConnectionOption(
            name="options",
            display_name="Command-line options",
            description=(
                "Command-line options to send to the server when the connection starts"
            ),
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="Server",
        ),
        ConnectionOption(
            name="applicationName",
            display_name="Application name",
            description='Value for the "application_name" configuration parameter',
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="Client",
            special_value_type=ConnectionOption.SPECIAL_VALUE_APP_NAME,
        ),
        ConnectionOption(
            name="sslmode",
            display_name="SSL mode",
            description="The SSL mode to use when connecting",
            value_type=ConnectionOption.VALUE_TYPE_CATEGORY,
            group_name="SSL",
            category_values=[
                CategoryValue("Disable", "disable"),
                CategoryValue("Allow", "allow"),
                CategoryValue("Prefer", "prefer"),
                CategoryValue("Require", "require"),
                CategoryValue("Verify-CA", "verify-ca"),
                CategoryValue("Verify-Full", "verify-full"),
            ],
            default_value="prefer",
        ),
        ConnectionOption(
            name="sslcompression",
            display_name="Use SSL compression",
            description="Whether to compress SSL connections",
            value_type=ConnectionOption.VALUE_TYPE_BOOLEAN,
            group_name="SSL",
        ),
        ConnectionOption(
            name="sslcert",
            display_name="SSL certificate filename",
            description="The filename of the SSL certificate to use",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="SSL",
        ),
        ConnectionOption(
            name="sslkey",
            display_name="SSL key filename",
            description="The filename of the key to use for the SSL certificate",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="SSL",
        ),
        ConnectionOption(
            name="sslrootcert",
            display_name="SSL root certificate filename",
            description="The filename of the SSL root CA certificate to use",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="SSL",
        ),
        ConnectionOption(
            name="sslcrl",
            display_name="SSL CRL filename",
            description="The filename of the SSL certificate revocation list to use",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="SSL",
        ),
        ConnectionOption(
            name="requirepeer",
            display_name="Require peer",
            description="The required username of the server process",
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="Server",
        ),
        ConnectionOption(
            name="service",
            display_name="Service name",
            description=(
                "The service name in pg_service.conf to use for connection parameters"
            ),
            value_type=ConnectionOption.VALUE_TYPE_STRING,
            group_name="Client",
        ),
    ]
)

capabilities = DMPServerCapabilities(
    "1.0",
    "PGSQL",
    "PostgreSQL",
    pg_conn_provider_opts,
    [BACKUP_OPTIONS, RESTORE_OPTIONS, SERIALIZATION_OPTIONS],
)
