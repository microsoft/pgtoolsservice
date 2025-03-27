# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing constants used throughout the service"""

PG_PROVIDER_NAME = "PGSQL"
MSSQL_PROVIDER_NAME = "MSSQL"

SUPPORTED_PROVIDERS = [PG_PROVIDER_NAME]

# DEFAULT_DB keys
COSMOS_PG_DEFAULT_DB = "COSMOSPGSQL"
PG_DEFAULT_DB = PG_PROVIDER_NAME

DEFAULT_DB = {PG_DEFAULT_DB: "postgres", COSMOS_PG_DEFAULT_DB: "citus"}

DEFAULT_PORT = {
    PG_PROVIDER_NAME: 5432,
}

DEFAULT_CONNECT_TIMEOUT = 10

# Default maximum connections per ConnectionDetails (server+db+params)
DEFAULT_MAX_CONNECTIONS = 10

# Service names
ADMIN_SERVICE_NAME = "admin"
CAPABILITIES_SERVICE_NAME = "capabilities"
CONNECTION_SERVICE_NAME = "connection"
DISASTER_RECOVERY_SERVICE_NAME = "disaster_recovery"
LANGUAGE_SERVICE_NAME = "language_service"
METADATA_SERVICE_NAME = "metadata"
OBJECT_EXPLORER_NAME = "object_explorer"
QUERY_EXECUTION_SERVICE_NAME = "query_execution"
SCRIPTING_SERVICE_NAME = "scripting"
WORKSPACE_SERVICE_NAME = "workspace"
EDIT_DATA_SERVICE_NAME = "edit_data"
TASK_SERVICE_NAME = "tasks"
CHAT_SERVICE_NAME = "chat"
SCHEMA_EDITOR_NAME = "schema_editor"
