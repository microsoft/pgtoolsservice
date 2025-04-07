# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from logging import Logger

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.object_explorer.object_explorer_service import ObjectExplorerService
from ossdbtoolsservice.utils import constants
import ossdbtoolsservice.utils.validate as validate
from ossdbtoolsservice.utils.connection import get_connection_details_with_defaults
from ossdbtoolsservice.schema import utils as schema_utils

from ossdbtoolsservice.connection.contracts import ConnectionDetails

from ossdbtoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType
from ossdbtoolsservice.hosting import Service, ServiceProvider
from ossdbtoolsservice.hosting.context import RequestContext
from ossdbtoolsservice.schema.session import SchemaEditorSession

from ossdbtoolsservice.schema.contracts import (
        GET_SCHEMA_MODEL_REQUEST,
        CREATE_SESSION_REQUEST,
        CLOSE_SESSION_REQUEST,
        SessionIdContainer,
)


class SchemaEditorService(Service):
    """Service for browsing database schemas"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None
        self._conn_service: ConnectionService | None = None
        self._logger: Logger | None = None
        self._session_map: dict[str, SchemaEditorSession] = {}
        self._session_lock: threading.Lock = threading.Lock()
        self._connect_semaphore = threading.Semaphore(1)


    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider
        self._logger = self._service_provider.logger

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(
            CREATE_SESSION_REQUEST, self._handle_create_session_request
        )
        self._service_provider.server.set_request_handler(
            GET_SCHEMA_MODEL_REQUEST, self._handle_get_schema_model_request
        )
        self._service_provider.server.set_request_handler(
            CLOSE_SESSION_REQUEST, self._handle_close_session_request
        )
        self._service_provider.server.add_shutdown_handler(
            self._handle_shutdown
        )

        # Find the provider type
        self._provider: str = self._service_provider.provider

        if self._service_provider.logger is not None:
            self._service_provider.logger.info(
                "Schema Editor service successfully initialized"
            )

        self._conn_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )


    @property
    def service_provider(self) -> ServiceProvider:
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        return self._service_provider


    def _handle_create_session_request(
        self, request_context: RequestContext, params: ConnectionDetails
    ) -> None:
        """Handle a create object explorer session request"""

        try:
            self._create_session(request_context, params)
        except Exception as e:
            message = f"Failed to create Schema Designer session: {str(e)}"
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
            return


    def _create_session(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        if self._logger:
            self._logger.info(f" [handler] Creating OE session for {params.server_name}")

        # Make sure we have the appropriate session params
        validate.is_not_none("params", params)

        params = get_connection_details_with_defaults(params)

        # Generate the session ID and create/store the session
        session_id = schema_utils.generate_session_uri(params)
        owner_uri = ObjectExplorerService._generate_session_uri(params)

        if self._logger:
            self._logger.info(f"   - Session ID: {session_id}")

        # Add the session to session map in a lock to
        # prevent race conditions between check and add
        with self._session_lock:
            if session_id in self._session_map:
                message = f"Schema Designer session for {session_id} already exists."
                # If session already exists, get it and respond with it
                if self.service_provider.logger is not None:
                    self.service_provider.logger.info(message)
                request_context.send_error(message)
            else:
                # If session doesn't exist, create a new one
                session = SchemaEditorSession(session_id, owner_uri)
                self._session_map[session_id] = session
                session.initialize(request_context)

        if self._logger:
            self._logger.info(f"   - Session created: {session_id}")

        return

    
    def _handle_get_schema_model_request(
        self, request_context: RequestContext, params: SessionIdContainer
    ) -> None:
        """Handle a get schema model request"""

        try:
            validate.is_not_none("session_id", params)
            session_id = params.session_id
            with self._session_lock:
                assert(session_id in self._session_map)
                session = self._session_map[session_id]
                assert(session.init_task is None)
            connection = self._conn_service.get_connection(
                session.owner_uri, ConnectionType.OBJECT_EXLPORER
            )
            if not connection:
                request_context.send_error(f"No connection available for {session.owner_uri}")
                return    
            session.get_schema_model(request_context, connection)
        except Exception as e:
            message = f"Failed to get schema model: {str(e)}"
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
            return
        return

    def _handle_close_session_request(
        self, request_context: RequestContext, params: SessionIdContainer
    ) -> None:
        try:
            validate.is_not_none("session_id", params)
            session_id = params.session_id
            with self._session_lock:
                assert(session_id in self._session_map)
                session = self._session_map.pop(session_id)
                session.close_session()
        except Exception as e:
            message = f"Failed to close session: {str(e)}"
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
            return
        return

    def _handle_shutdown(self) -> None:
        """Close all designer sessions when service is shutdown"""
        if self.service_provider.logger is not None:
            self.service_provider.logger.info("Closing all the Schema Designer sessions")
        
        """
        Nothing to do here really, since we reuse the OE connection to the DB
        """
        return