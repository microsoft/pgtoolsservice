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
            if (scripting_operation == ScriptOperation.Select.value):
                return self.script_as_select(connection, metadata)
            script_map = self._script_map(connection)
            object_type = metadata["metadataTypeName"]
            return script_map[object_type][scripting_operation](metadata)
        except Exception:
            return "Scripting Operation not supported"

    def _script_map(self, connection) -> dict:
        """ Maps every object and operation to the correct script function """
        scripter = Scripter(connection)
        create = ScriptOperation.Create.value
        delete = ScriptOperation.Delete.value
        update = ScriptOperation.Update.value
        return {
            "Table": {
                create: scripter.get_table_create_script,
                delete: scripter.get_table_delete_script,
                update: scripter.get_table_update_script
            },
            "View": {
                create: scripter.get_view_create_script,
                delete: scripter.get_view_delete_script,
                update: scripter.get_view_update_script
            },
            "Schema": {
                create: scripter.get_schema_create_script,
                delete: scripter.get_schema_delete_script,
                update: scripter.get_schema_update_script
            },
            "Database": {
                create: scripter.get_database_create_script,
                delete: scripter.get_database_delete_script,
            },
            "Role": {
                create: scripter.get_role_create_script,
                update: scripter.get_role_update_script
            }
        }
