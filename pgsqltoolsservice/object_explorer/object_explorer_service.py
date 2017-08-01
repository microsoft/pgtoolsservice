# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from typing import Dict     # noqa
from urllib.parse import quote

from pgsmo import Server
from pgsqltoolsservice.connection.contracts import ConnectRequestParams, ConnectionDetails, ConnectionType
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.object_explorer.contracts import (
    NodeInfo,
    CreateSessionResponse, CREATE_SESSION_REQUEST, SessionCreatedParameters, SESSION_CREATED_METHOD,
    CLOSE_SESSION_REQUEST,
    ExpandParameters, EXPAND_REQUEST,
    ExpandCompletedParameters, EXPAND_COMPLETED_METHOD,
    REFRESH_REQUEST
)
from pgsqltoolsservice.object_explorer.routing import route_request
from pgsqltoolsservice.object_explorer.session import ObjectExplorerSession
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
import pgsqltoolsservice.utils as utils


class ObjectExplorerService(object):
    """Service for browsing database objects"""

    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._session_map: Dict[str, 'ObjectExplorerSession'] = {}
        self._session_lock: threading.Lock = threading.Lock()

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the request handlers with the server
        self._service_provider.server.set_request_handler(CREATE_SESSION_REQUEST, self._handle_create_session_request)
        self._service_provider.server.set_request_handler(CLOSE_SESSION_REQUEST, self._handle_close_session_request)
        self._service_provider.server.set_request_handler(EXPAND_REQUEST, self._handle_expand_request)
        self._service_provider.server.set_request_handler(REFRESH_REQUEST, self._handle_refresh_request)

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Object Explorer service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        """Handle a create object explorer session request"""
        # Step 1: Create the session
        try:
            # Make sure we have the appropriate session params
            utils.validate.is_not_none('params', params)

            # Generate the session ID and create/store the session
            session_id = self._generate_session_uri(params)
            session: ObjectExplorerSession = ObjectExplorerSession(session_id, params)

            # Add the session to session map in a lock to prevent race conditions between check and add
            with self._session_lock:
                if session_id in self._session_map:
                    # TODO: Localize
                    raise NameError(f'Object explorer session for {session_id} already exists!')

                self._session_map[session_id] = session

            # Respond that the session was created
            response = CreateSessionResponse(session_id)
            request_context.send_response(response)

        except Exception as e:
            request_context.send_error(str(e))
            return

        # Step 2: Connect the session and lookup the root node asynchronously
        try:
            session.init_task = threading.Thread(target=self._initialize_session, args=(request_context, session))
            session.init_task.setDaemon(False)
            session.init_task.start()
        except Exception as e:
            # TODO: Localize
            self._session_created_error(request_context, session, f'Failed to start OE init task: {str(e)}')

    def _handle_close_session_request(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        """Handle close Object Explorer" sessions request"""
        try:
            utils.validate.is_not_none('params', params)

            # Generate the session ID and try to remove the session
            session_id = self._generate_session_uri(params)
            session = self._session_map.pop(session_id, None)
            # TODO: Dispose session (disconnect, etc)

            request_context.send_response(session is not None)
        except Exception as e:
            message = f'Failed to close OE session: {str(e)}'
            if self._service_provider.logger is not None:
                self._service_provider.logger.error(message)
            request_context.send_error(message)

    def _handle_refresh_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle refresh Object Explorer create node request"""
        # connection_details = self._session_map[params.session_id]
        request_context.send_response(True)

    def _handle_expand_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle expand Object Explorer tree node request"""
        # Step 1: Find the session
        try:
            utils.validate.is_not_none('params', params)
            utils.validate.is_not_none_or_whitespace('params.node_path', params.node_path)
            utils.validate.is_not_none_or_whitespace('params.session_id', params.session_id)

            session = self._session_map.get(params.session_id)
            if session is None:
                raise ValueError(f'OE session with ID {params.session_id} does not exist')   # TODO: Localize

            request_context.send_response(True)
        except Exception as e:
            request_context.send_error(f'Failed to expand node: {str(e)}')  # TODO: Localize
            return

        # Step 2: Start a task for expanding the node
        try:
            expand_task = threading.Thread(target=self._expand_node, args=(request_context, params, session))
            expand_task.setDaemon(False)
            expand_task.start()
            session.expand_tasks.append(expand_task)
        except Exception as e:
            self._expand_node_error(request_context, params, str(e))

    # PRIVATE HELPERS ######################################################
    def _expand_node(self, request_context: RequestContext, params: ExpandParameters, session: ObjectExplorerSession):
        try:
            response = ExpandCompletedParameters(session.id, params.node_path)
            response.node_path = params.node_path
            response.nodes = route_request(session, params.node_path)

            request_context.send_notification(EXPAND_COMPLETED_METHOD, response)
        except Exception as e:
            self._expand_node_error(request_context, params, str(e))

    def _initialize_session(self, request_context: RequestContext, session: ObjectExplorerSession):
        conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        connection = None

        try:
            # Step 1: Connect with the provided connection details
            connect_request = ConnectRequestParams(
                session.connection_details,
                session.id,
                ConnectionType.OBJECT_EXLPORER
            )
            connect_result = conn_service.connect(connect_request)
            if connect_result is None:
                raise RuntimeError('Connection was cancelled during connect')   # TODO Localize
            if connect_result.error_message is not None:
                raise RuntimeError(connect_result.error_message)

            # Step 2: Store the connection in the session
            connection = conn_service.get_connection(session.id, ConnectionType.OBJECT_EXLPORER)

            # Step 3: Create the PGSMO Server object for the session and create the root node for the server
            session.server = Server(connection)
            metadata = ObjectMetadata.from_data(0, 'Database', session.connection_details.options['dbname'])
            node = NodeInfo()
            node.label = session.connection_details.options['dbname']
            node.is_leaf = False
            node.node_path = session.id
            node.node_type = 'Database'
            node.metadata = metadata

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
            message = f'Failed to initialize object explorer session: {str(e)}'  # TODO Localize
            self._session_created_error(request_context, session, message)

            # Attempt to clean up the connection
            if connection is not None:
                conn_service.disconnect(session.id, ConnectionType.OBJECT_EXLPORER)

    def _session_created_error(self, request_context: RequestContext, session: ObjectExplorerSession, message: str):
        if self._service_provider.logger is not None:
            self._service_provider.logger.warning(f'OE service errored while creating session: {message}')

        # Create error notification
        response = SessionCreatedParameters()
        response.success = False
        response.session_id = session.id
        response.root_node = None
        response.error_message = message
        request_context.send_notification(SESSION_CREATED_METHOD, response)

        # Clean up the session from the session map
        self._session_map.pop(session.id)

    def _expand_node_error(self, request_context: RequestContext, params: ExpandParameters, message: str):
        if self._service_provider.logger is not None:
            self._service_provider.logger.warning(f'OE service errored while expanding node: {message}')

        response = ExpandCompletedParameters(params.session_id, params.node_path)
        response.error_message = f'Failed to expand node: {message}'    # TODO: Localize

        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    @staticmethod
    def _generate_session_uri(params: ConnectionDetails) -> str:
        # Make sure the required params are provided
        utils.validate.is_not_none_or_whitespace('params.server_name', params.options.get('host'))
        utils.validate.is_not_none_or_whitespace('params.user_name', params.options.get('user'))
        utils.validate.is_not_none_or_whitespace('params.database_name', params.options.get('dbname'))

        # Generates a session ID that will function as the base URI for the session
        host = quote(params.options['host'])
        user = quote(params.options['user'])
        db = quote(params.options['dbname'])

        return f'objectexplorer://{user}@{host}:{db}/'
