# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.scripting.scripter import Scripter
from pgsqltoolsservice.scripting.contracts import (
    ScriptAsParameters, ScriptAsResponse, SCRIPTAS_REQUEST, ScriptOperation
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.utils import constants


class ScriptingService(object):
    """Service for scripting database objects"""

    def __init__(self):
        self._service_provider: ServiceProvider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            SCRIPTAS_REQUEST, self._handle_scriptas_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Scripting service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_scriptas_request(self, request_context: RequestContext, params: ScriptAsParameters) -> None:
        try:
            metadata = params.metadata
            scripting_operation = params.operation
            connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
            connection = connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)
            script = self._scripting_operation(scripting_operation, connection, metadata)
            request_context.send_response(ScriptAsResponse(params.owner_uri, script))
        except Exception as e:
            request_context.send_error(str(e), params)

    # HELPER FUNCTIONS ######################################################

    def script_as_select(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for select operations """
        scripter = Scripter(connection)
        return scripter.script_as_select(metadata)

    def _scripting_operation(self, scripting_operation: int, connection, metadata: ObjectMetadata):
        """Helper function to get the correct script based on operation"""
        try:
            script_map = self._script_map(connection, metadata)
            return script_map[scripting_operation]
        except Exception:
            object_type = metadata["metadataTypeName"]
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception(f'{ScriptOperation(scripting_operation)} failed for {object_type}')
            return "Scripting Operation not supported"

    def _script_map(self, connection, metadata) -> dict:
        """ Maps every object and operation to the correct script function """
        scripter = Scripter(connection)
        create = ScriptOperation.Create.value
        delete = ScriptOperation.Delete.value
        update = ScriptOperation.Update.value
        select = ScriptOperation.Select.value
        return {
            create: scripter.get_create_script(metadata),
            delete: scripter.get_delete_script(metadata),
            update: scripter.get_update_script(metadata),
            select: self.script_as_select(connection, metadata)
        }
