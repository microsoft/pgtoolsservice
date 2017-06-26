# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.object_explorer.contracts import (CreateSessionParameters, CREATE_SESSION_REQUEST)
import pgsqltoolsservice.utils as utils

class ObjectExplorerService(object):
    """Service for browsing database objects"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            CREATE_SESSION_REQUEST, self._handle_create_session_request
        )
   
        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Object Explorer service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(self, request_context: RequestContext, params: CreateSessionParameters) -> None:

 
        request_context.send_response(True)

