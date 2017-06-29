# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from typing import List
from urllib.parse import quote 

import psycopg2
import psycopg2.errorcodes

from pgsqltoolsservice.connection.contracts import ConnectRequestParams, ConnectionDetails, ConnectionType
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.object_explorer.contracts import (
    CreateSessionParameters, CreateSessionResponse, CREATE_SESSION_REQUEST,
    CloseSessionParameters, CLOSE_SESSION_REQUEST,
    ExpandParameters, EXPAND_REQUEST,
    ExpandCompletedParameters, EXPAND_COMPLETED_METHOD,
    SessionCreatedParameters, SESSION_CREATED_METHOD,
    NodeInfo)
from pgsqltoolsservice.metadata.contracts import ObjectMetadata
import pgsqltoolsservice.utils as utils
from pgsmo.objects.server.server import Server
from pgsmo.objects.database.database import Database
from pgsmo.objects.schema.schema import Schema
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View

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
        session_id = self._generate_uri(params)
        
        self._create_oe_connection(params, session_id)

        dbname = params.options['dbname']
        self.cur_dbname = dbname
        #root_path = params.options['host'] + '/' + params.options['dbname']

        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'Database'
        metadata.name = dbname
        metadata.schema = None

        node = NodeInfo()
        node.label = dbname
        node.isLeaf = False
        node.node_path = 'sqltools100/wideworldimporters'
        node.node_type = 'Database'
        node.metadata = metadata

        response = SessionCreatedParameters()
        response.session_id = session_id
        response.root_node = node

        request_context.send_response(CreateSessionResponse(session_id))
        request_context.send_notification(SESSION_CREATED_METHOD, response)


    def _create_oe_connection(self, params: CreateSessionParameters, session_id: str) -> None:
        details = ConnectionDetails.from_data(params.options['host'], params.options['dbname'], 
            params.options['user'], params.options)
        connect_request = ConnectRequestParams(details, session_id)

        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        
        connection_service._connect(connect_request)


    def _handle_close_session_request(self, request_context: RequestContext, params: CreateSessionParameters) -> None:
        request_context.send_response(True)


    def _handle_expand_request(self, request_context: RequestContext, params: ExpandParameters) -> None:
        nodes: List[NodeInfo] = None
        if params.node_path == 'sqltools100/wideworldimporters/Views':
            nodes = self._get_view_nodes(params.session_id)
        elif params.node_path == 'sqltools100/wideworldimporters/Tables':
            nodes = self._get_table_nodes(params.session_id)
        else:
            nodes = self._get_folder_nodes()        

        response = ExpandCompletedParameters()        
        response.session_id = params.session_id
        response.node_path = params.node_path 
        response.nodes = nodes

        request_context.send_response(True)
        request_context.send_notification(EXPAND_COMPLETED_METHOD, response)

    def _get_database(self, session_id: str) -> Database:
        # Retrieve the connection service
        connection_service = self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]
        if connection_service is None:
            raise LookupError('Connection service could not be found')  # TODO: Localize
        conn = connection_service.get_connection(session_id, ConnectionType.DEFAULT)

        server = Server(conn)
        database = None
        for cur_db in server.databases:
            if cur_db.name == self.cur_dbname:
                database = cur_db

        return database


    def _get_folder_nodes(self) -> List[NodeInfo]:        
        table_node = NodeInfo()
        table_node.label = 'Tables'
        table_node.isLeaf = False
        table_node.node_path = 'sqltools100/wideworldimporters/Tables'
        table_node.node_type = 'Folder'

        view_node = NodeInfo()
        view_node.label = 'Views'
        view_node.isLeaf = False
        view_node.node_path = 'sqltools100/wideworldimporters/Views'
        view_node.node_type = 'Folder'
        return [ table_node, view_node ]


    def _get_view_nodes(self, session_id: str) -> List[NodeInfo]:
        database = self._get_database(session_id)

        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'View'
        metadata.name = 'spt_values'
        metadata.schema = 'dbo'

        view_node = NodeInfo()
        view_node.label = 'View Item 1'
        view_node.isLeaf = True
        view_node.node_path = 'sqltools100/wideworldimporters/Views/ViewItem1'
        view_node.node_type = 'View'
        view_node.metadata = metadata
        return [ view_node ]


    def _get_table_nodes(self, session_id: str) -> List[NodeInfo]:
        database = self._get_database(session_id)

        metadata = ObjectMetadata()
        metadata.metadata_type = 0
        metadata.metadata_type_name = 'View'
        metadata.name = 'spt_values'
        metadata.schema = 'dbo'

        node_list: List[NodeInfo] = []
        for cur_schema in database.schemas:
            for cur_table in cur_schema.tables:
                cur_node = NodeInfo()
                cur_node.label = cur_schema.name + '.' + cur_table.name
                cur_node.isLeaf = True
                cur_node.node_path = 'sqltools100/wideworldimporters/Tables/' + cur_node.label
                cur_node.node_type = 'Table'
                cur_node.metadata = metadata
                node_list.append(cur_node)
        return node_list


    def _generate_uri(self, params: CreateSessionParameters) -> str:
        uri = 'objectexplorer://' + quote(params.options['host'])
        if (params.options['dbname'] != None):
            uri +=  ';' + 'databaseName=' + params.options['dbname']

        if (params.options['user'] != None):   
            uri +=  ';' + 'user=' + params.options['user']

        return uri


        #   internal static string GenerateUri(ConnectionDetails details)
        # {
        #     Validate.IsNotNull("details", details);
        #     string uri = string.Format(CultureInfo.InvariantCulture, "{0}{1}", uriPrefix, Uri.EscapeUriString(details.ServerName));
        #     uri = AppendIfExists(uri, "databaseName", details.DatabaseName);
        #     uri = AppendIfExists(uri, "user", details.UserName);
        #     return uri;
        # }


        #         ['host']:'10.128.18.175'
        # ['dbname']:'TestDb'
        # ['user']:'postgres'
        # ['password']:'Katmai900'
        # ['applicationName']:'carbon'
