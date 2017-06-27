# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.admin.contracts import (
    GetDatabaseInfoParameters, GetDatabaseInfoResponse, GET_DATABASEINFO_REQUEST)
import pgsqltoolsservice.utils as utils

class AdminService(object):
    """Service for general database administration support"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            GET_DATABASEINFO_REQUEST, self._handle_get_databaseinfo_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Admin service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_get_databaseinfo_request(self, request_context: RequestContext, params: GetDatabaseInfoParameters) -> None:
        request_context.send_response(GetDatabaseInfoResponse())

