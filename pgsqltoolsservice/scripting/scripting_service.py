# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.scripting.scripter import Scripter
from pgsqltoolsservice.scripting.contracts import (
    ScriptAsParameters, ScriptAsResponse, SCRIPTAS_REQUEST, ScriptOperation)
from pgsqltoolsservice.connection.contracts import (
    ConnectionType)
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from pgsqltoolsservice.utils import constants
import pgsmo.utils.querying as querying

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
            connection = connection_service.get_connection(
                params.owner_uri, ConnectionType.QUERY)            
            script = self._scripting_operation(scripting_operation, connection, metadata)
            request_context.send_response(ScriptAsResponse(params.owner_uri, script))
        except Exception as e:
            request_context.send_error(str(e), params)

    # HELPER FUNCTIONS ######################################################

    def script_as_create(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for create operations """
        # convert connection to ServiceConnection Wrapper
        connection = querying.ServerConnection(connection)
        scripter = Scripter(connection)
        if (metadata["metadataTypeName"] == 'Database'):
            return scripter.get_database_create_script(metadata)
        elif (metadata["metadataTypeName"] == 'View'):
            return scripter.get_view_create_script(metadata)
        elif (metadata["metadataTypeName"] == 'Table'):
            return scripter.get_table_create_script(metadata)

    def script_as_insert(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for insert operations """
        return

    def script_as_select(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for select operations """
        connection = querying.ServerConnection(connection)
        scripter = Scripter(connection)
        return scripter.script_as_select(connection, metadata)
    
    def script_as_update(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for update operations """
        connection = querying.ServerConnection(connection)
        scripter = Scripter(connection)
        metadataType = metadata["metadataTypeName"]
        if (metadataType == 'View'):
            return scripter.get_view_update_script(metadata)
        elif (metadataType == 'Table'):
            return scripter.get_table_update_script(metadata)

    def script_as_delete(self, connection, metadata: ObjectMetadata) -> str:
        """ Function to get script for insert operations """
        # convert connection to ServiceConnection Wrapper
        connection = querying.ServerConnection(connection)
        scripter = Scripter(connection)
        metadataType = metadata["metadataTypeName"]
        if (metadataType == 'Database'):
            return scripter.get_database_delete_script(metadata)
        elif (metadataType == 'View'):
            return scripter.get_view_delete_script(metadata)
        elif (metadataType == 'Table'):
            return scripter.get_table_delete_script(metadata)

    def _scripting_operation(self, scripting_operation: ScriptOperation, connection, metadata: ObjectMetadata) -> None:
        """Helper function to get the correct script based on operation"""
        if (scripting_operation == ScriptOperation.Select):
            return self.script_as_select(connection, metadata)
        elif (scripting_operation == ScriptOperation.Create):
            return self.script_as_create(connection, metadata)
        elif (scripting_operation == ScriptOperation.Insert):
            return self.script_as_insert(connection, metadata)
        elif (scripting_operation == ScriptOperation.Update):
            return self.script_as_update(connection, metadata)
        elif (scripting_operation == ScriptOperation.Delete):
            return self.script_as_delete(connection, metadata)
        else:
            return None