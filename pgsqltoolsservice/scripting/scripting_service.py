# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, Dict       # noqa

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.scripting.scripter import Scripter
from pgsqltoolsservice.scripting.contracts import (
    ScriptAsParameters, ScriptAsResponse, SCRIPTAS_REQUEST, ScriptOperation
)
from pgsqltoolsservice.connection.contracts import ConnectionType
from pgsqltoolsservice.metadata.contracts.object_metadata import ObjectMetadata     # noqa
import pgsqltoolsservice.utils as utils


class ScriptingService(object):
    """Service for scripting database objects"""
    def __init__(self):
        self._service_provider: ServiceProvider = None

        self._script_map: Dict[ScriptOperation, Callable[[Scripter, ObjectMetadata], str]] = {
            ScriptOperation.CREATE: lambda scripter, metadata: scripter.get_create_script(metadata),
            ScriptOperation.DELETE: lambda scripter, metadata: scripter.get_delete_script(metadata),
            ScriptOperation.UPDATE: lambda scripter, metadata: scripter.get_update_script(metadata),
            ScriptOperation.SELECT: lambda scripter, metadata: scripter.script_as_select(metadata)
        }

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(SCRIPTAS_REQUEST, self._handle_scriptas_request)

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Scripting service successfully initialized')

    # REQUEST HANDLERS #####################################################
    def _handle_scriptas_request(self, request_context: RequestContext, params: ScriptAsParameters) -> None:
        try:
            utils.validate.is_not_none('params', params)

            scripting_operation = params.operation
            connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
            connection = connection_service.get_connection(params.owner_uri, ConnectionType.QUERY)

            scripter = Scripter(connection)
            script = self._script_map[scripting_operation](scripter, params.metadata)
            request_context.send_response(ScriptAsResponse(params.owner_uri, script))
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.exception('Scripting operation failed')
            request_context.send_error(str(e), params)
