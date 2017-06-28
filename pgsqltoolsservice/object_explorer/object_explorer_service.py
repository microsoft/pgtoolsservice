# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.object_explorer.contracts import (
    CreateSessionParameters, CreateSessionResponse, CREATE_SESSION_REQUEST,
    CloseSessionParameters, CLOSE_SESSION_REQUEST,
    ExpandParameters, EXPAND_REQUEST,
    SessionCreatedParameters, SESSION_CREATED_METHOD,
    NodeInfo)
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
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

        self._service_provider.server.set_request_handler(
            CLOSE_SESSION_REQUEST, self._handle_close_session_request
        )

        self._service_provider.server.set_request_handler(
            EXPAND_REQUEST, self._handle_expand_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Object Explorer service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(self, request_context: RequestContext, params: CreateSessionParameters) -> None:        
        session_id = 'objectexplorer://1'

        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Database'
        metadata.name = 'testdb'
        metadata.schema = None

        node = NodeInfo()
        node.label = 'testdb'
        node.isLeaf = False
        node.node_path = 'sqltools100/wideworldimporters'
        node.node_type = 'Database'

        response = SessionCreatedParameters()
        response.session_id = session_id
        response.root_node = node

        request_context.send_response(CreateSessionResponse(session_id))
        request_context.send_notification(SESSION_CREATED_METHOD, response)


    def _handle_close_session_request(self, request_context: RequestContext, params: CreateSessionParameters) -> None:
        request_context.send_response(True)


    def _handle_expand_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        request_context.send_response(True)
