# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional      # noqa

from ossdbtoolsservice.exception.OssdbErrorConstants import OssdbErrorConstants
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider
from ossdbtoolsservice.metadata.contracts.object_metadata import ObjectMetadata
from ossdbtoolsservice.scripting.scripter import Scripter
from ossdbtoolsservice.scripting.contracts import (
    ScriptAsParameters, ScriptAsResponse, SCRIPTAS_REQUEST
)
from ossdbtoolsservice.connection.contracts import ConnectionType
import ossdbtoolsservice.utils as utils


class ScriptingService(object):
    """Service for scripting database objects"""

    def __init__(self):
        self._service_provider: Optional[ServiceProvider] = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(SCRIPTAS_REQUEST, self._handle_scriptas_request)

        # Find the provider type
        self._provider: str = self._service_provider.provider

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Scripting service successfully initialized')

    def create_metadata(self, params: ScriptAsParameters):
        """Helper function to convert a ScriptingObjects into ObjectMetadata"""
        scripting_object = params.scripting_objects[0]
        object_metadata = ObjectMetadata()
        object_metadata.metadata_type_name = scripting_object["type"]
        object_metadata.schema = scripting_object["schema"]
        object_metadata.name = scripting_object["name"]
        return object_metadata

    # REQUEST HANDLERS #####################################################
    def _handle_scriptas_request(self, request_context: RequestContext, params: ScriptAsParameters) -> None:
        try:
            utils.validate.is_not_none('params', params)

            scripting_operation = params.operation
            connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
            connection = connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)
            object_metadata = self.create_metadata(params)

            scripter = Scripter(connection)

            script = scripter.script(scripting_operation, object_metadata)
            request_context.send_response(ScriptAsResponse(params.owner_uri, script))
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Scripting operation failed')
            request_context.send_error(message=str(e), data=params, code=OssdbErrorConstants.SCRIPTAS_REQUEST_ERROR)
