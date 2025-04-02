# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.core.server_connection import ServerConnection
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.scripting.contracts import (
    SCRIPT_AS_REQUEST,
    ScriptAsParameters,
    ScriptAsResponse,
)
from ossdbtoolsservice.scripting.scripter import Scripter
from ossdbtoolsservice.utils import constants, validate


class ScriptingService(Service):
    """Service for scripting database objects"""

    def __init__(self) -> None:
        self._service_provider: Optional[ServiceProvider] = None

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            SCRIPT_AS_REQUEST, self._handle_script_as_request
        )

        # Find the provider type
        self._provider: str = self._service_provider.provider

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Scripting service successfully initialized")

    # REQUEST HANDLERS #####################################################
    def _handle_script_as_request(
        self,
        request_context: RequestContext,
        params: ScriptAsParameters,
        retry_state: bool = False,
    ) -> None:
        try:
            validate.is_not_none("params", params)
        except Exception as e:
            self._request_error(request_context, params, e)
            return

        connection: ServerConnection | None = None
        try:
            scripting_operation = params.operation
            if scripting_operation is None:
                raise Exception("Operation is required")

            owner_uri = params.owner_uri
            if owner_uri is None:
                raise Exception("Owner URI is required")

            scripting_objects = params.scripting_objects
            if scripting_objects is None or len(scripting_objects) == 0:
                raise Exception("Scripting objects are required")

            connection_service = self.service_provider.get(
                constants.CONNECTION_SERVICE_NAME, ConnectionService
            )
            pooled_connection = connection_service.get_pooled_connection(owner_uri)

            if pooled_connection is None:
                raise Exception("Could not get connection")

            object_metadata = scripting_objects[0]

            with pooled_connection as connection:
                scripter = Scripter(connection)
                script = scripter.script(scripting_operation, object_metadata)

            request_context.send_response(ScriptAsResponse(owner_uri, script))
        except Exception as e:
            if connection is not None and connection.connection.broken and not retry_state:
                self._log_warning(
                    "Server closed the connection unexpectedly. Attempting to reconnect..."
                )
                self._handle_script_as_request(request_context, params, True)
            else:
                self._request_error(request_context, params, e)

    def _request_error(
        self, request_context: RequestContext, params: ScriptAsParameters, exc: Exception
    ) -> None:
        self._log_exception(exc)
        request_context.send_error(str(exc), params)
