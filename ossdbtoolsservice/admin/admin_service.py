# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.admin.contracts import (
    DatabaseInfo,
    GetDatabaseInfoParameters,
    GetDatabaseInfoResponse,
    GET_DATABASE_INFO_REQUEST,
)
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider, Service
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.driver import ServerConnection


class AdminService(Service):
    """Service for general database administration support"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            GET_DATABASE_INFO_REQUEST, self._handle_get_database_info_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Admin service successfully initialized")

    # REQUEST HANDLERS #####################################################

    def _handle_get_database_info_request(
        self, request_context: RequestContext, params: GetDatabaseInfoParameters
    ) -> None:
        # Retrieve the connection from the connection service
        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        connection: ServerConnection = connection_service.get_connection(
            params.owner_uri, ConnectionType.DEFAULT
        )

        # Get database owner
        owner_result = connection.get_database_owner()
        size_result = connection.get_database_size(connection.database_name)

        # Set up and send the response
        options = {
            DatabaseInfo.DBNAME: connection.database_name,
            DatabaseInfo.OWNER: owner_result,
            DatabaseInfo.SIZE: size_result,
        }
        request_context.send_response(GetDatabaseInfoResponse(DatabaseInfo(options)))
