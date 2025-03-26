# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.driver.types import ServerConnection
from ossdbtoolsservice.workspace.contracts import Configuration


class ConnectionManager:
    """Wrapper class that handles connections"""

    def __init__(
        self, provider: str, config: Configuration, conn_options: dict[str, str | int]
    ) -> None:
        # Get info about this connection's provider
        self._provider = provider

        # Create a connection using the provider and connection options
        self._conn_object = self._create_connection(conn_options, config)

    def _create_connection(
        self, options: dict[str, str | int], config: Configuration | None
    ) -> ServerConnection:
        """
        Creates a ServerConnection according to the provider and connection options
        :param options: a dict containing connection parameters
        """

        return ServerConnection(options, config)

    def get_connection(self) -> ServerConnection:
        return self._conn_object
