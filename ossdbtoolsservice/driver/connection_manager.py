# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict

from ossdbtoolsservice.utils.constants import (
    PG_PROVIDER_NAME
)
from ossdbtoolsservice.driver.types import ServerConnection, PostgreSQLConnection
from ossdbtoolsservice.workspace.contracts import Configuration


class ConnectionManager:
    """Wrapper class that handles different types of drivers and connections """

    CONNECTORS = {
        PG_PROVIDER_NAME: PostgreSQLConnection
    }

    def __init__(self, provider: str, config: Configuration, conn_options: Dict[str, str]):

        # Get info about this connection's provider
        self._provider = provider

        # Create a connection using the provider and connection options
        self._conn_object = self._create_connection(conn_options, config)

    def _create_connection(self, options, config) -> ServerConnection:
        """
        Creates a ServerConnection according to the provider and connection options
        :param options: a dict containing connection parameters
        """
        if self._provider not in self.CONNECTORS.keys():
            raise AssertionError(str(self._provider) + " is not a supported database engine.")

        return self.CONNECTORS[self._provider](options, config)

    def get_connection(self):
        return self._conn_object
