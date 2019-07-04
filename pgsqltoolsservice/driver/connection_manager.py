# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABC, abstractmethod
from pgsqltoolsservice.utils.constants import PG_PROVIDER_NAME, MYSQL_PROVIDER_NAME
from pgsqltoolsservice.driver.types import *

class ConnectionManager:
    """Wrapper class that handles different types of drivers and connections """

    def __init__(self, provider, params):

        # Get info about this connection's provider
        self._provider = provider

        # Create a connection using the provider and connection options
        self._conn_object = self._create_connection(params.connection.options)

    def _create_connection(self, options) -> ServerConnection:
        """
        Creates a ServerConnection according to the provider and connection options
        :param options: a dict containing connection parameters
        """
        if self._provider == PG_PROVIDER_NAME:
            return PsycopgConnection(options)
        elif self._provider == MYSQL_PROVIDER_NAME:
            return PyMySQLConnection(options)
        else:
            raise AssertionError(str(self._provider) + " is not a supported database engine.")

    def get_connection(self):
        return self._conn_object