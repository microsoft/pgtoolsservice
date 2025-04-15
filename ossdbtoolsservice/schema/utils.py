# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from urllib.parse import quote

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.utils import validate


def generate_session_uri(params: ConnectionDetails) -> str:
    # Make sure the required params are provided
    server_name = validate.is_not_none_or_whitespace(
        "params.server_name", params.server_name
    )
    user_name = validate.is_not_none_or_whitespace("params.user_name", params.user_name)
    database_name = validate.is_not_none_or_whitespace(
        "params.database_name", params.database_name
    )
    port = validate.is_not_none("params.port", params.port)

    # Generates a session ID that will function as the base URI for the session
    host = quote(server_name)
    user = quote(user_name)
    db = quote(database_name)
    # Port number distinguishes between connections to different server
    # instances with the same username, dbname running on same host
    port_str = quote(str(port))

    return f"schemadesigner://{user}@{host}:{port_str}:{db}/"