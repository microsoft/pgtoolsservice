# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from urllib.parse import quote
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
        self._session_map: dict = dict()

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

        self._service_provider.server.set_request_handler(
            REFRESH_REQUEST, self._handle_refresh_request
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info('Object Explorer service successfully initialized')

    # REQUEST HANDLERS #####################################################

    def _handle_create_session_request(self, request_context: RequestContext, params: ConnectionDetails) -> None:
        """Handle a create object explorer session request"""

        # validate that input parameters are as expected
        if not self._are_create_session_params_valid(params):
            request_context.send_response(None)
            return

        # generate a session id and create a dedicated Object Explorer connection
        session_id = self._generate_uri(params)
        connection_details = self._create_oe_connection(params, session_id)
        self._session_map[session_id] = connection_details

        # create database node metadata object
        dbname = params.options['dbname']
        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Database'
        metadata.name = dbname
        metadata.schema = None

        # create database tree node
        node = NodeInfo()
        node.label = dbname
        node.isLeaf = False
        node.node_path = self._get_root_path(connection_details)
        node.node_type = 'Database'
        node.metadata = metadata

        # create response notification notification
        response = SessionCreatedParameters()
        response.session_id = session_id
        response.root_node = node

        # send request return code and session created notification
        request_context.send_response(CreateSessionResponse(session_id))
        request_context.send_notification(SESSION_CREATED_METHOD, response)

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
        if params.node_path == root_path + '/Views':
            nodes = self._get_view_nodes(params.session_id, root_path)
        elif params.node_path == root_path + '/Tables':
            nodes = self._get_table_nodes(params.session_id, root_path)
        elif params.node_path == root_path + '/Functions':
            nodes = self._get_function_nodes(params.session_id, root_path)
        else:
            nodes = self._get_folder_nodes(root_path)

        response = ExpandCompletedParameters()
        response.session_id = params.session_id
        response.node_path = params.node_path
        response.nodes = nodes

        request_context.send_response(True)
        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    def _are_create_session_params_valid(self, params: ConnectionDetails) -> bool:
        return params is not None and params.options is not None and params.options['host'] is not None

    def _get_root_path(self, connection_details: ConnectionDetails) -> str:
        return connection_details.server_name[0] + '/' + connection_details.database_name[0]

    def _create_oe_connection(self, params: ConnectionDetails, session_id: str) -> ConnectionDetails:
        details = ConnectionDetails.from_data(params.options['host'], params.options['dbname'],
                                              params.options['user'], params.options)
        connect_request = ConnectRequestParams(details, session_id)

        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        connection_service._connect(connect_request)
        return details

    def _get_database(self, session_id: str) -> Database:
        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        conn = connection_service.get_connection(session_id, ConnectionType.DEFAULT)

        connection_details = self._session_map[session_id]
        dbname = connection_details.database_name[0]
        server = Server(conn)
        return server.databases[dbname]

    def _get_folder_nodes(self, root_path: str) -> List[NodeInfo]:
        function_node = NodeInfo()
        function_node.label = 'Functions'
        function_node.isLeaf = False
        function_node.node_path = root_path + '/Functions'
        function_node.node_type = 'Folder'

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

        return [function_node, table_node, view_node]

    def _get_function_nodes(self, session_id: str, root_path: str) -> List[NodeInfo]:
        database = self._get_database(session_id)
        node_list: List[NodeInfo] = []
        for schema in database.schemas:
            for func in schema.functions:
                metadata = ObjectMetadata()
                metadata.metadata_type = 0
                metadata.metadata_type_name = 'Function'
                metadata.name = func.name
                metadata.schema = schema.name

                node = NodeInfo()
                node.label = f'{schema.name}.{func.name}'
                node.isLeaf = True
                node.node_path = f'{root_path}/Functions/{node.label}'
                node.node_type = 'Function'
                node.metadata = metadata
                node_list.append(node)
        return node_list

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

    def _generate_uri(self, params: ConnectionDetails) -> str:
        uri = 'objectexplorer://' + quote(params.options['host'])
        if (params.options['dbname'] is not None):
            uri += ';' + 'databaseName=' + params.options['dbname']
        if (params.options['user'] is not None):
            uri += ';' + 'user=' + params.options['user']
        return uri
