# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from logging import Logger

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.hosting import Service, ServiceProvider
from ossdbtoolsservice.hosting.context import RequestContext
from ossdbtoolsservice.schema.contracts import (
    CLOSE_SESSION_REQUEST,
    CREATE_SESSION_REQUEST,
    GET_SCHEMA_MODEL_REQUEST,
    SessionIdContainer,
)
from ossdbtoolsservice.schema.session import SchemaEditorSession
from ossdbtoolsservice.utils import constants


class SchemaEditorService(Service):
    """Service for browsing database schemas"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider
        self._conn_service: ConnectionService
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

    def _handle_create_session_request(
        self, request_context: RequestContext, params: SessionIdContainer
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

    def _create_session(
            self, request_context: RequestContext, params: SessionIdContainer
        ) -> None:
        session_id = params.session_id
        if self._logger:
            self._logger.info(f" [handler] Creating session for {session_id}")

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
                session = SchemaEditorSession(session_id)
                self._session_map[session_id] = session
                request_context.send_response(params)
                session.initialize(request_context)

        if self._logger:
            self._logger.info(f"   - Session created: {session_id}")

        return

    def _handle_get_schema_model_request(
        self, request_context: RequestContext, params: SessionIdContainer
    ) -> None:
        """Handle a get schema model request"""

        try:
            session_id = params.session_id
            with self._session_lock:
                assert (session_id in self._session_map)
                session = self._session_map[session_id]
                assert (session.init_task is None)
            connection_pool = self._conn_service.get_pooled_connection(
                session_id)
            if not connection_pool:
                request_context.send_error(
                    f"No connection available for {session_id}")
                return
            with connection_pool as connection:
                session.get_schema_model(request_context, connection)
            request_context.send_response(params)
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
            session_id = params.session_id
            with self._session_lock:
                assert (session_id in self._session_map)
                session = self._session_map.pop(session_id)
                session.close_session()
        except Exception as e:
            message = f"Failed to close session: {str(e)}"
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
        return

    def _handle_shutdown(self) -> None:
        """Close all designer sessions when service is shutdown"""
        if self.service_provider.logger is not None:
            self.service_provider.logger.info(
                "Closing all the Schema Designer sessions")

        with self._session_lock:
            for session in self._session_map.values():
                session.close_session()
        return
