# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import functools
import threading
from typing import Dict, Optional, List     # noqa
from urllib.parse import quote, urlparse

from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.connection.contracts import ConnectRequestParams, ConnectionDetails, ConnectionType
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider
from ossdbtoolsservice.object_explorer.contracts import (
    NodeInfo,
    CreateSessionResponse, CREATE_SESSION_REQUEST, SessionCreatedParameters, SESSION_CREATED_METHOD,
    CloseSessionParameters, CLOSE_SESSION_REQUEST,
    ExpandParameters, EXPAND_REQUEST,
    ExpandCompletedParameters, EXPAND_COMPLETED_METHOD,
    REFRESH_REQUEST
)
from ossdbtoolsservice.object_explorer.session import ObjectExplorerSession
from ossdbtoolsservice.metadata.contracts import ObjectMetadata
import ossdbtoolsservice.utils as utils

from pgsmo import Server as PGServer
from mysqlsmo import Server as MySQLServer

from ossdbtoolsservice.object_explorer.routing import PG_ROUTING_TABLE, MYSQL_ROUTING_TABLE

ROUTING_TABLES = {
    utils.constants.MYSQL_PROVIDER_NAME: MYSQL_ROUTING_TABLE,
    utils.constants.PG_PROVIDER_NAME: PG_ROUTING_TABLE
}

SERVER_TYPES = {
    utils.constants.MYSQL_PROVIDER_NAME: MySQLServer,
    utils.constants.PG_PROVIDER_NAME: PGServer
}


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
        self._service_provider.server.add_shutdown_handler(self._handle_shutdown)

        # Find the provider type
        self._provider: str = self._service_provider.provider

        # Find the routing table to use
        self._routing_table = ROUTING_TABLES[self._service_provider.provider]

        # Find the type of server to use
        self._server = SERVER_TYPES[self._provider]

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Object Explorer service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        """Handle a create object explorer session request"""
        # Step 1: Create the session
        try:
            # Make sure we have the appropriate session params
            utils.validate.is_not_none('params', params)

            # Use the provider's default db if db name was not specified
            if params.database_name is None or params.database_name == '':
                if self._provider == utils.constants.MYSQL_PROVIDER_NAME:
                    params.database_name = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME].configuration.my_sql.default_database
                elif self._provider == utils.constants.PG_PROVIDER_NAME:
                    params.database_name = self._service_provider[utils.constants.WORKSPACE_SERVICE_NAME].configuration.pgsql.default_database

            # Use the provider's default port if port number was not specified
            if not params.port:
                params.port = utils.constants.DEFAULT_PORT[self._provider]

            # Generate the session ID and create/store the session
            session_id = self._generate_session_uri(params, self._provider)
            session: ObjectExplorerSession = ObjectExplorerSession(session_id, params)

            # Add the session to session map in a lock to prevent race conditions between check and add
            with self._session_lock:
                if session_id in self._session_map:
                    # Removed the exception for now. But we need to investigate why we would get this
                    if self._service_provider.logger is not None:
                        self._service_provider.logger.error(f'Object explorer session for {session_id} already exists!')
                    request_context.send_response(False)
                    return

                self._session_map[session_id] = session

            # Respond that the session was created
            response = CreateSessionResponse(session_id)
            request_context.send_response(response)

        except Exception as e:
            message = f'Failed to create OE session: {str(e)}'
            if self._service_provider.logger is not None:
                self._service_provider.logger.error(message)
            request_context.send_error(message)
            return

        # Step 2: Connect the session and lookup the root node asynchronously
        try:
            session.init_task = threading.Thread(target=self._initialize_session, args=(request_context, session))
            session.init_task.daemon = True
            session.init_task.start()
        except Exception as e:
            # TODO: Localize
            self._session_created_error(request_context, session, f'Failed to start OE init task: {str(e)}')

    def _handle_close_session_request(self, request_context: RequestContext, params: CloseSessionParameters) -> None:
        """Handle close Object Explorer" sessions request"""
        try:
            utils.validate.is_not_none('params', params)

            # Try to remove the session
            session = self._session_map.pop(params.session_id, None)
            if session is not None:
                self._close_database_connections(session)
                conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
                connect_result = conn_service.disconnect(session.id, ConnectionType.OBJECT_EXLPORER)

                if not connect_result:
                    if self._service_provider.logger is not None:
                        self._service_provider.logger.info(f'Could not close the OE session with Id {session.id}')
                    request_context.send_response(False)
                else:
                    request_context.send_response(True)
            else:
                request_context.send_response(False)
        except Exception as e:
            message = f'Failed to close OE session: {str(e)}'   # TODO: Localize
            if self._service_provider.logger is not None:
                self._service_provider.logger.error(message)
            request_context.send_error(message)

    def _handle_refresh_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle refresh Object Explorer create node request"""
        self._expand_node_base(True, request_context, params)

    def _handle_expand_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle expand Object Explorer tree node request"""
        self._expand_node_base(False, request_context, params)

    def _handle_shutdown(self) -> None:
        """Close all OE sessions when service is shutdown"""
        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Closing all the OE sessions')
        conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        for key, session in self._session_map.items():
            connect_result = conn_service.disconnect(session.id, ConnectionType.OBJECT_EXLPORER)
            self._close_database_connections(session)
            if connect_result:
                if self._service_provider.logger is not None:
                    self._service_provider.logger.info('Closed the OE session with Id: ' + session.id)
            else:
                if self._service_provider.logger is not None:
                    self._service_provider.logger.info('Could not close the OE session with Id: ' + session.id)

    # PRIVATE HELPERS ######################################################

    def _close_database_connections(self, session: 'ObjectExplorerSession') -> None:
        conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        for database in session.server.databases:
            close_result = conn_service.disconnect(session.id + database.name, ConnectionType.OBJECT_EXLPORER)
            if not close_result:
                if self._service_provider.logger is not None:
                    self._service_provider.logger.info(f'could not close the connection for the database {database.name}')

    def _expand_node_base(self, is_refresh: bool, request_context: RequestContext, params: ExpandParameters):
        # Step 1: Find the session
        session = self._get_session(request_context, params)
        if session is None:
            return

        # Step 2: Start a task for expanding the node
        try:
            key = params.node_path
            if is_refresh:
                task = session.refresh_tasks.get(key)
            else:
                task = session.expand_tasks.get(key)

            if task is not None and task.is_alive():
                return

            new_task = threading.Thread(target=self._expand_node_thread, args=(is_refresh, request_context, params, session))
            new_task.daemon = True
            new_task.start()

            if is_refresh:
                session.refresh_tasks[key] = new_task
            else:
                session.expand_tasks[key] = new_task

        except Exception as e:
            self._expand_node_error(request_context, params, str(e))

    def _expand_node_thread(self, is_refresh: bool, request_context: RequestContext, params: ExpandParameters, session: ObjectExplorerSession):
        try:
            response = ExpandCompletedParameters(session.id, params.node_path)
            response.nodes = self._route_request(is_refresh, session, params.node_path)

            request_context.send_notification(EXPAND_COMPLETED_METHOD, response)
        except Exception as e:
            self._expand_node_error(request_context, params, str(e))

    def _expand_node_error(self, request_context: RequestContext, params: ExpandParameters, message: str):
        if self._service_provider.logger is not None:
            self._service_provider.logger.warning(f'OE service errored while expanding node: {message}')

        response = ExpandCompletedParameters(params.session_id, params.node_path)
        response.error_message = f'Failed to expand node: {message}'    # TODO: Localize

        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    def _get_session(self, request_context: RequestContext, params: ExpandParameters) -> Optional[ObjectExplorerSession]:
        try:
            utils.validate.is_not_none('params', params)
            utils.validate.is_not_none_or_whitespace('params.node_path', params.node_path)
            utils.validate.is_not_none_or_whitespace('params.session_id', params.session_id)

            session = self._session_map.get(params.session_id)
            if session is None:
                raise ValueError(f'OE session with ID {params.session_id} does not exist')   # TODO: Localize

            if not session.is_ready:
                raise ValueError(f'Object Explorer session with ID {params.session_id} is not ready, yet.')     # TODO: Localize

            request_context.send_response(True)
            return session
        except Exception as e:
            message = f'Failed to expand node: {str(e)}'    # TODO: Localize
            if self._service_provider.logger is not None:
                self._service_provider.logger.error(message)
            request_context.send_error(message)
            return

    def _create_connection(self, session: ObjectExplorerSession, database_name: str) -> Optional[ServerConnection]:
        conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]

        options = session.connection_details.options.copy()
        options['dbname'] = database_name
        conn_details = ConnectionDetails.from_data(options)

        key_uri = session.id + database_name
        connect_request = ConnectRequestParams(conn_details, key_uri, ConnectionType.OBJECT_EXLPORER)
        connect_result = conn_service.connect(connect_request)
        if connect_result.error_message is not None:
            raise RuntimeError(connect_result.error_message)

        connection = conn_service.get_connection(key_uri, ConnectionType.OBJECT_EXLPORER)
        return connection

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

            # Step 2: Get the connection to use for object explorer
            connection = conn_service.get_connection(session.id, ConnectionType.OBJECT_EXLPORER)

            # Step 3: Create the Server object for the session and create the root node for the server
            session.server = self._server(connection, functools.partial(self._create_connection, session))
            metadata = ObjectMetadata(session.server.urn_base, None, 'Database', session.server.maintenance_db_name)
            node = NodeInfo()
            node.label = session.connection_details.database_name
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

    @staticmethod
    def _generate_session_uri(params: ConnectionDetails, provider_name: str) -> str:
        # Make sure the required params are provided
        utils.validate.is_not_none_or_whitespace('params.server_name', params.options.get('host'))
        utils.validate.is_not_none_or_whitespace('params.user_name', params.options.get('user'))
        # database_name is not required for mysql connection
        if provider_name == utils.constants.PG_PROVIDER_NAME:
            utils.validate.is_not_none_or_whitespace('params.database_name', params.options.get('dbname'))
        utils.validate.is_not_none('params.port', params.options.get('port'))

        # Generates a session ID that will function as the base URI for the session
        host = quote(params.options['host'])
        user = quote(params.options['user'])
        db = quote(params.options['dbname'])
        # Port number distinguishes between connections to different server
        # instances with the same username, dbname running on same host
        port = quote(str(params.options['port']))

        return f'objectexplorer://{user}@{host}:{port}:{db}/'

    def _route_request(self, is_refresh: bool, session: ObjectExplorerSession, path: str) -> List[NodeInfo]:
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
        if is_refresh or (path not in session.cache.keys()):
            # Find a matching route for the path
            for route, target in self._routing_table.items():
                match = route.match(path)
                if match is not None:
                    # We have a match!
                    if is_refresh:
                        # Invalidate cache for all paths with current path as suffix
                        self._remove_path_from_session_cache(session, path)
                    target_nodes = target.get_nodes(is_refresh, path, session, match.groupdict())
                    session.cache[path] = target_nodes
                    return target_nodes

            # If this node is a leaf
            if not path.endswith("/"):
                return []
            # If we make it to here, there isn't a route that matches the path
            raise ValueError(f'Path {path} does not have a matching OE route')  # TODO: Localize
        else:
            # Return the results of a previous request for the same path
            return session.cache[path]
    
    def _remove_path_from_session_cache(self, session: ObjectExplorerSession, path: str) -> None:
        updated_cache = {key:value for key, value in session.cache.items() if key.startswith(path) == False}
        session.cache = updated_cache
