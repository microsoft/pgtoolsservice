# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from typing import Dict, List, Optional
from urllib.parse import quote

from psycopg2.extensions import connection as ppg2_connection

from pgsqltoolsservice.connection.contracts import ConnectRequestParams, ConnectionDetails, ConnectionType
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.object_explorer.contracts import (
    CreateSessionResponse, CREATE_SESSION_REQUEST,
    CLOSE_SESSION_REQUEST,
    ExpandParameters, EXPAND_REQUEST,
    ExpandCompletedParameters, EXPAND_COMPLETED_METHOD,
    SessionCreatedParameters, SESSION_CREATED_METHOD,
    REFRESH_REQUEST, NodeInfo)
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
import pgsqltoolsservice.utils as utils
from pgsmo.objects.server.server import Server
from pgsmo.objects.database.database import Database


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
            session = ObjectExplorerSession(session_id, params)

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
            request_context.send_error(e)
            return

        # Step 2: Connect the session and lookup the root node asynchronously
        try:
            session.init_task = threading.Thread(target=self._initialize_session(request_context, session))
            session.init_task.setDaemon(False)
            session.init_task.start()
        except Exception as e:
            if self._service_provider.logger is not None:
                self._service_provider.logger.error(f'Failed to start OE init task: {e}')

    def _handle_close_session_request(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        """Handle close Object Explorer" sessions request"""
        request_context.send_response(True)

    def _handle_refresh_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle refresh Object Explorer create node request"""
        # connection_details = self._session_map[params.session_id]
        request_context.send_response(True)

    def _handle_expand_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        """Handle expand Object Explorer tree node request"""

        connection_details = self._session_map[params.session_id]
        root_path = self._get_root_path(connection_details)

        # the below dispatch switch block needs to be replaced with some type of look map so it can
        # easily scale to all the different types of items that may be in the OE tree (TODO: karlb 7/5/2017)
        nodes: List[NodeInfo] = None
        if params.node_path == root_path + '/Views':
            nodes = self._get_view_nodes(params.session_id, root_path)
        elif params.node_path == root_path + '/Tables':
            nodes = self._get_table_nodes(params.session_id, root_path)
        else:
            nodes = self._get_folder_nodes(root_path)

        response = ExpandCompletedParameters()
        response.session_id = params.session_id
        response.node_path = params.node_path
        response.nodes = nodes

        request_context.send_response(True)
        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    def _get_root_path(self, connection_details: ConnectionDetails) -> str:
        return connection_details.server_name[0] + '/' + connection_details.database_name[0]

    def _get_database(self, session_id: str) -> Database:
        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        conn = connection_service.get_connection(session_id, ConnectionType.DEFAULT)

        connection_details = self._session_map[session_id]
        dbname = connection_details.database_name[0]
        server = Server(conn)
        database = None
        for cur_db in server.databases:
            if cur_db.name == dbname:
                database = cur_db

        return database

    def _get_folder_nodes(self, root_path: str) -> List[NodeInfo]:
        table_node = NodeInfo()
        table_node.label = 'Tables'
        table_node.isLeaf = False
        table_node.node_path = root_path + '/Tables'
        table_node.node_type = 'Folder'

        view_node = NodeInfo()
        view_node.label = 'Views'
        view_node.isLeaf = False
        view_node.node_path = root_path + '/Views'
        view_node.node_type = 'Folder'
        return [table_node, view_node]

    def _get_view_nodes(self, session_id: str, root_path: str) -> List[NodeInfo]:
        database = self._get_database(session_id)
        node_list: List[NodeInfo] = []
        for cur_schema in database.schemas:
            for cur_view in cur_schema.views:
                metadata = ObjectMetadata()
                metadata.metadata_type = 0
                metadata.metadata_type_name = 'View'
                metadata.name = cur_view.name
                metadata.schema = cur_schema.name

                cur_node = NodeInfo()
                cur_node.label = cur_schema.name + '.' + cur_view.name
                cur_node.isLeaf = True
                cur_node.node_path = root_path + '/Views/' + cur_node.label
                cur_node.node_type = 'View'
                cur_node.metadata = metadata
                node_list.append(cur_node)
        return node_list

    def _get_table_nodes(self, session_id: str, root_path: str) -> List[NodeInfo]:
        database = self._get_database(session_id)
        node_list: List[NodeInfo] = []
        for cur_schema in database.schemas:
            for cur_table in cur_schema.tables:
                metadata = ObjectMetadata()
                metadata.metadata_type = 0
                metadata.metadata_type_name = 'Table'
                metadata.name = cur_table.name
                metadata.schema = cur_schema.name

                cur_node = NodeInfo()
                cur_node.label = cur_schema.name + '.' + cur_table.name
                cur_node.isLeaf = True
                cur_node.node_path = root_path + '/Tables/' + cur_node.label
                cur_node.node_type = 'Table'
                cur_node.metadata = metadata
                node_list.append(cur_node)
        return node_list

    # PRIVATE HELPERS ######################################################
    def _initialize_session(self, request_context: RequestContext, session: ObjectExplorerSession):
        conn_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]

        try:
            # Step 1: Connect with the provided connection details
            connect_request = ConnectRequestParams(session.id, session.connection_details, ConnectionType.OBJECT_EXLPORER)
            connect_result = conn_service.connect(connect_request)
            if connect_result is None:
                raise RuntimeError('Connection was cancelled during connect')   # TODO Localize
            if connect_result.error_message is not None:
                raise RuntimeError(connect_result.error_message)

            # Step 2: Store the connection in the session
            connection = conn_service.get_connection(session.id, ConnectionType.OBJECT_EXLPORER)
            session.connection = connection

            # Step 3: Create the PGSMO Server object for the session and create the root node for the server
            session.server = Server(connection)
            metadata = ObjectMetadata.from_data(0, 'Database', session.connection_details.database_name)
            node = NodeInfo()
            node.label = session.connection_details.database_name
            node.isLeaf = False
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

        except Exception as e:
            # Return a notification that an error occurred
            response = SessionCreatedParameters()
            response.success = False
            response.session_id = session.id
            response.root_node = None
            response.error_message = f'Failed to initialize object explorer session: {e}'    # TODO Localize
            request_context.send_notification(SESSION_CREATED_METHOD, response)

            # Attempt to clean up the connection
            if session.connection is not None:
                conn_service.disconnect(session.id, ConnectionType.OBJECT_EXLPORER)

    @staticmethod
    def _generate_session_uri(params: ConnectionDetails) -> str:
        # Make sure the required params are provided
        utils.validate.is_not_none_or_whitespace('params.server_name', params.server_name)
        utils.validate.is_not_none_or_whitespace('params.user_name', params.user_name)
        utils.validate.is_not_none_or_whitespace('params.database_name', params.database_name)

        # Generates a session ID that will function as the base URI for the session
        host = quote(params.server_name)
        user = quote(params.user_name)
        db = quote(params.database_name)

        return f'objectexplorer://{user}@{host}:{db}/'


class ObjectExplorerSession:
    def __init__(self, session_id: str, params: ConnectionDetails):
        self.connection: Optional[ppg2_connection] = None
        self.connection_details: ConnectionDetails = params
        self.id: str = session_id
        self.is_ready: bool = False
        self.server: Optional[Server] = None

        self.init_task: Optional[threading.Thread] = None
        self.expand_task: Optional[threading.Thread] = None
