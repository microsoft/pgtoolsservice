# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from logging import Logger
from typing import Dict, List, Optional  # noqa
from urllib.parse import quote, urlparse

import psycopg

import ossdbtoolsservice.utils.constants as constants
import ossdbtoolsservice.utils.validate as validate
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts import (
    ConnectionDetails,
    ConnectionType,
    ConnectRequestParams,
)
from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.hosting import RequestContext, Service, ServiceProvider
from ossdbtoolsservice.metadata.contracts import ObjectMetadata
from ossdbtoolsservice.object_explorer.contracts import (
    CLOSE_SESSION_REQUEST,
    CREATE_SESSION_REQUEST,
    EXPAND_COMPLETED_METHOD,
    EXPAND_REQUEST,
    REFRESH_REQUEST,
    SESSION_CREATED_METHOD,
    CloseSessionParameters,
    CreateSessionResponse,
    ExpandCompletedParameters,
    ExpandParameters,
    NodeInfo,
    SessionCreatedParameters,
)
from ossdbtoolsservice.object_explorer.contracts.close_session_request import (
    CloseSessionResponse,
)
from ossdbtoolsservice.object_explorer.contracts.get_session_id_request import (
    GET_SESSION_ID_REQUEST,
    GetSessionIdResponse,
)
from ossdbtoolsservice.object_explorer.routing import PG_ROUTING_TABLE
from ossdbtoolsservice.object_explorer.session import ObjectExplorerSession
from ossdbtoolsservice.utils.connection import get_connection_details_with_defaults
from pgsmo import Server as PGServer

ROUTING_TABLES = {constants.PG_PROVIDER_NAME: PG_ROUTING_TABLE}

SERVER_TYPES = {constants.PG_PROVIDER_NAME: PGServer}


class ObjectExplorerService(Service):
    """Service for browsing database objects"""

    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None
        self._logger: Logger | None = None
        self._session_map: dict[str, ObjectExplorerSession] = {}
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
            CLOSE_SESSION_REQUEST, self._handle_close_session_request
        )
        self._service_provider.server.set_request_handler(
            EXPAND_REQUEST, self._handle_expand_request
        )
        self._service_provider.server.set_request_handler(
            REFRESH_REQUEST, self._handle_refresh_request
        )
        self._service_provider.server.set_request_handler(
            GET_SESSION_ID_REQUEST, self._handle_get_session_id_request
        )

        self._service_provider.server.add_shutdown_handler(self._handle_shutdown)

        # Find the provider type
        self._provider: str = self._service_provider.provider

        self._routing_table = PG_ROUTING_TABLE

        if self._service_provider.logger is not None:
            self._service_provider.logger.info(
                "Object Explorer service successfully initialized"
            )

    @property
    def service_provider(self) -> ServiceProvider:
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        return self._service_provider

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(
        self, request_context: RequestContext, params: ConnectionDetails
    ) -> None:
        """Handle a create object explorer session request"""
        # Step 1: Create the session
        session_exist_check = False
        if self._logger:
            self._logger.info(f" [handler] Creating OE session for {params.server_name}")
        try:
            # Make sure we have the appropriate session params
            validate.is_not_none("params", params)

            params = get_connection_details_with_defaults(params)

            # Generate the session ID and create/store the session
            session_id = self._generate_session_uri(params)

            if self._logger:
                self._logger.info(f"   - Session ID: {session_id}")

            # Add the session to session map in a lock to
            # prevent race conditions between check and add
            with self._session_lock:
                if session_id in self._session_map:
                    # If session already exists, get it and respond with it
                    session_exist_check = True
                    if self.service_provider.logger is not None:
                        self.service_provider.logger.info(
                            f"Object explorer session for {session_id} already exists. "
                            "Returning existing session."
                        )
                    session = self._session_map[session_id]
                else:
                    # If session doesn't exist, create a new one
                    session = ObjectExplorerSession(session_id, params)
                    self._session_map[session_id] = session

            if self._logger:
                self._logger.info(f"   - Session created: {session_id}")

            # Respond that the session was created (or existing session was returned)
            response = CreateSessionResponse(sessionId=session_id)
            request_context.send_response(response)

        except Exception as e:
            message = f"Failed to create OE session: {str(e)}"
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
            return

        # Step 2: Connect the session and lookup the root node asynchronously
        try:
            if not session_exist_check:
                session.init_task = threading.Thread(
                    target=self._initialize_session, args=(request_context, session)
                )
                session.init_task.daemon = True
                session.init_task.start()
        except Exception as e:
            # TODO: Localize
            self._session_created_error(
                request_context, session, f"Failed to start OE init task: {str(e)}"
            )

    def _handle_close_session_request(
        self, request_context: RequestContext, params: CloseSessionParameters
    ) -> None:
        """Handle close Object Explorer" sessions request"""
        try:
            validate.is_not_none("params", params)

            session_id = params.session_id
            if session_id is None or session_id == "":
                raise ValueError("Session ID is required")

            # Try to remove the session
            session = self._session_map.pop(session_id, None)
            if session is not None:
                self._close_database_connections(session)
                conn_service = self.service_provider.get(
                    constants.CONNECTION_SERVICE_NAME, ConnectionService
                )
                connect_result = conn_service.disconnect(
                    session.id, ConnectionType.OBJECT_EXLPORER
                )

                if not connect_result:
                    if self.service_provider.logger is not None:
                        self.service_provider.logger.info(
                            f"Could not close the OE session with Id {session.id}"
                        )
                    request_context.send_response(
                        CloseSessionResponse(sessionId=session_id, success=False)
                    )
                else:
                    request_context.send_response(
                        CloseSessionResponse(sessionId=session_id, success=True)
                    )
            else:
                request_context.send_response(
                    CloseSessionResponse(sessionId=session_id, success=False)
                )
        except Exception as e:
            message = f"Failed to close OE session: {str(e)}"  # TODO: Localize
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)

    def _handle_get_session_id_request(
        self, request_context: RequestContext, params: ConnectionDetails
    ) -> None:
        """Retrieve the existing session ID for the given connection details"""
        validate.is_not_none("params", params)
        params = get_connection_details_with_defaults(params)

        session_id = self._generate_session_uri(params)

        if self._logger:
            self._logger.info(f"   - Session ID: {session_id}")

        request_context.send_response(GetSessionIdResponse(sessionId=session_id))

    def _handle_refresh_request(
        self, request_context: RequestContext, params: ExpandParameters
    ) -> None:
        """Handle refresh Object Explorer create node request"""
        self._expand_node_base(True, request_context, params)

    def _handle_expand_request(
        self, request_context: RequestContext, params: ExpandParameters
    ) -> None:
        """Handle expand Object Explorer tree node request"""
        self._expand_node_base(False, request_context, params)

    def _handle_shutdown(self) -> None:
        """Close all OE sessions when service is shutdown"""
        if self.service_provider.logger is not None:
            self.service_provider.logger.info("Closing all the OE sessions")
        conn_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        for _key, session in self._session_map.items():
            connect_result = conn_service.disconnect(
                session.id, ConnectionType.OBJECT_EXLPORER
            )
            self._close_database_connections(session)
            if connect_result:
                if self.service_provider.logger is not None:
                    self.service_provider.logger.info(
                        "Closed the OE session with Id: " + session.id
                    )
            else:
                if self.service_provider.logger is not None:
                    self.service_provider.logger.info(
                        "Could not close the OE session with Id: " + session.id
                    )

    # PRIVATE HELPERS ######################################################

    def _close_database_connections(self, session: "ObjectExplorerSession") -> None:
        conn_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        for database in session.server.databases if session.server else []:
            close_result = False
            try:
                close_result = conn_service.disconnect(
                    session.id + database.name, ConnectionType.OBJECT_EXLPORER
                )
            except psycopg.OperationalError as e:
                if self.service_provider.logger is not None:
                    self.service_provider.logger.info(
                        "could not close the connection for the "
                        f"database {database.name}: {e}"
                    )
            if not close_result:
                self._log_info(
                    f"could not close the connection for the database {database.name}"
                )

    def _expand_node_base(
        self,
        is_refresh: bool,
        request_context: RequestContext,
        params: ExpandParameters,
    ) -> None:
        # Step 1: Find the session
        session = self._get_session(request_context, params)
        if session is None:
            return

        try:
            # Step 2: Start a task for expanding the node
            key = params.node_path
            if key is None:
                raise ValueError("Node path is required")
            if is_refresh:
                task = session.refresh_tasks.get(key)
            else:
                task = session.expand_tasks.get(key)

            if task is not None and task.is_alive():
                return

            new_task = threading.Thread(
                target=self._expand_node_thread,
                args=(is_refresh, request_context, params, session),
            )
            new_task.daemon = True
            new_task.start()

            if is_refresh:
                session.refresh_tasks[key] = new_task
            else:
                session.expand_tasks[key] = new_task
        except Exception as e:
            self._expand_node_error(request_context, params, str(e))

    def _expand_node_thread(
        self,
        is_refresh: bool,
        request_context: RequestContext,
        params: ExpandParameters,
        session: ObjectExplorerSession,
        retry_state: bool = False,
    ) -> None:
        try:
            node_path = params.node_path
            if node_path is None:
                raise ValueError("Node path is required")
            response = ExpandCompletedParameters(session.id, node_path)
            response.nodes = self._route_request(is_refresh, session, node_path)

            request_context.send_notification(EXPAND_COMPLETED_METHOD, response)
        except BaseException as e:
            if (
                session.server
                and session.server.connection is not None
                and session.server.connection.connection.broken
                and not retry_state
            ):
                conn_service = self.service_provider.get(
                    constants.CONNECTION_SERVICE_NAME, ConnectionService
                )
                connection = conn_service.get_connection(
                    session.id, ConnectionType.OBJECT_EXLPORER
                )
                if connection is not None:
                    session.server.set_connection(connection)
                    session.server.refresh()
                    self._expand_node_thread(
                        is_refresh, request_context, params, session, True
                    )
                    return
                else:
                    self._expand_node_error(request_context, params, str(e))
            else:
                self._expand_node_error(request_context, params, str(e))

    def _expand_node_error(
        self, request_context: RequestContext, params: ExpandParameters, message: str
    ) -> None:
        if self.service_provider.logger is not None:
            self.service_provider.logger.warning(
                f"OE service errored while expanding node: {message}"
            )

        response = ExpandCompletedParameters(params.session_id or "", params.node_path or "")
        response.error_message = f"Failed to expand node: {message}"  # TODO: Localize

        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    def _get_session(
        self, request_context: RequestContext, params: ExpandParameters
    ) -> Optional[ObjectExplorerSession]:
        try:
            validate.is_not_none("params", params)
            validate.is_not_none_or_whitespace("params.node_path", params.node_path)
            session_id = validate.is_not_none_or_whitespace(
                "params.session_id", params.session_id
            )

            session = self._session_map.get(session_id)
            if session is None:
                raise ValueError(
                    f"OE session with ID {session_id} does not exist"
                )  # TODO: Localize

            if not session.is_ready:
                if session.init_task is not None and session.init_task.is_alive():
                    # If the initialization task is still running, wait for it to finish
                    session.init_task.join()
                else:
                    raise ValueError(
                        f"Object Explorer session with ID {session_id} is not ready, yet."
                    )  # TODO: Localize

            request_context.send_response(True)
            return session
        except Exception as e:
            message = f"Failed to expand node base: {str(e)}"  # TODO: Localize
            if self.service_provider.logger is not None:
                self.service_provider.logger.error(message)
            request_context.send_error(message)
            return None

    def _create_connection(
        self, session: ObjectExplorerSession, database_name: str
    ) -> Optional[ServerConnection]:
        conn_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )

        options = session.connection_details.options.copy()
        options["dbname"] = database_name
        conn_details = ConnectionDetails.from_data(options)

        key_uri = session.id + database_name
        connect_request = ConnectRequestParams(
            conn_details, key_uri, ConnectionType.OBJECT_EXLPORER
        )
        connect_result = conn_service.connect(connect_request)
        if connect_result is None:
            raise RuntimeError("Connection was cancelled during connect")
        if connect_result.error_message is not None:
            raise RuntimeError(connect_result.error_message)

        connection = conn_service.get_connection(key_uri, ConnectionType.OBJECT_EXLPORER)
        return connection

    def _initialize_session(
        self, request_context: RequestContext, session: ObjectExplorerSession
    ) -> None:
        conn_service = self.service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        connection = None

        try:
            # Step 1: Connect with the provided connection details
            with self._connect_semaphore:
                connect_request = ConnectRequestParams(
                    session.connection_details,
                    session.id,
                    ConnectionType.OBJECT_EXLPORER,
                )
                connect_result = conn_service.connect(connect_request)
                if connect_result is None:
                    raise RuntimeError(
                        "Connection was cancelled during connect"
                    )  # TODO Localize
                if connect_result.error_message is not None:
                    raise RuntimeError(connect_result.error_message)

            # Step 2: Get the connection to use for object explorer
            connection = conn_service.get_connection(
                session.id, ConnectionType.OBJECT_EXLPORER
            )
            if connection is None:
                raise RuntimeError("Connection was cancelled during connect")

            # Step 3: Create the Server object for the session and
            # create the root node for the server
            session.server = PGServer(
                connection, lambda dbname: self._create_connection(session, dbname)
            )
            metadata = ObjectMetadata(
                session.server.urn_base,
                None,
                "Database",
                session.server.maintenance_db_name,
            )
            node = NodeInfo(
                label=session.connection_details.database_name or "",
                node_path=session.id,
                node_type="Database",
                metadata=metadata,
                is_leaf=False,
            )

            # Step 4: Send the completion notification to the server
            response = SessionCreatedParameters()
            response.success = True
            response.session_id = session.id
            response.root_node = node
            response.error_message = None
            request_context.send_notification(SESSION_CREATED_METHOD, response)

            # Mark the session as complete
            session.is_ready = True

        except Exception as e:
            # Return a notification that an error occurred
            message = (
                f"Failed to initialize object explorer session: {str(e)}"  # TODO Localize
            )
            self._session_created_error(request_context, session, message)

            # Attempt to clean up the connection
            if connection is not None:
                conn_service.disconnect(session.id, ConnectionType.OBJECT_EXLPORER)

    def _session_created_error(
        self,
        request_context: RequestContext,
        session: ObjectExplorerSession,
        message: str,
    ) -> None:
        if self.service_provider.logger is not None:
            self.service_provider.logger.warning(
                f"OE service errored while creating session to {session.id}: {message}"
            )

        # Create error notification
        response = SessionCreatedParameters()
        response.success = False
        response.session_id = session.id
        response.root_node = None
        response.error_message = message
        request_context.send_notification(SESSION_CREATED_METHOD, response)

        # Clean up the session from the session map
        self._session_map.pop(session.id)

    @staticmethod
    def _generate_session_uri(params: ConnectionDetails) -> str:
        # Make sure the required params are provided
        server_name = validate.is_not_none_or_whitespace(
            "params.server_name", params.server_name
        )
        user_name = validate.is_not_none_or_whitespace("params.user_name", params.user_name)
        database_name = validate.is_not_none_or_whitespace(
            "params.database_name", params.database_name
        )
        port = validate.is_not_none("params.port", params.port)

        # Generates a session ID that will function as the base URI for the session
        host = quote(server_name)
        user = quote(user_name)
        db = quote(database_name)
        # Port number distinguishes between connections to different server
        # instances with the same username, dbname running on same host
        port_str = quote(str(port))

        return f"objectexplorer://{user}@{host}:{port_str}:{db}/"

    def _route_request(
        self, is_refresh: bool, session: ObjectExplorerSession, path: str
    ) -> list[NodeInfo]:
        """
        Performs a lookup for a given expand request
        :param is_refresh: Whether or not the request is a request to refresh or just expand
        :param session: Session that the expand is being performed on
        :param path: Path of the object to expand
        :return: List of nodes that result from the expansion
        """
        # Figure out what the path we're looking at is
        path = urlparse(path).path

        # We query if its a refresh request or this is the first expand request for this path
        if is_refresh or (path not in session.cache):
            # Find a matching route for the path
            for route, target in self._routing_table.items():
                match = route.match(path)
                if match is not None:
                    # We have a match!
                    target_nodes = target.get_nodes(
                        is_refresh, path, session, match.groupdict()
                    )
                    session.cache[path] = target_nodes
                    return target_nodes

            # If this node is a leaf
            if not path.endswith("/"):
                return []
            # If we make it to here, there isn't a route that matches the path
            raise ValueError(
                f"Path {path} does not have a matching OE route"
            )  # TODO: Localize
        else:
            # Return the results of a previous request for the same path
            return session.cache[path]
