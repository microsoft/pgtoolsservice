# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the connection service class, which allows for the user to connect and
disconnect and holds the current connection, if one is present"""

import logging
import threading
import uuid

import psycopg2

from pgsqltoolsservice.connection.contracts import (
    CONNECT_REQUEST, ConnectRequestParams,
    DISCONNECT_REQUEST, DisconnectRequestParams,
    CONNECTION_COMPLETE_METHOD, ConnectionCompleteParams,
    ConnectionDetails, ConnectionSummary, ConnectionType, ServerInfo,
    LIST_DATABASES_REQUEST, ListDatabasesParams, ListDatabasesResponse
)
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider


class ConnectionInfo(object):
    """Information pertaining to a unique connection instance"""

    def __init__(self, owner_uri: str, details: ConnectionDetails):
        self.owner_uri: str = owner_uri
        self.details: ConnectionDetails = details
        self.connection_id: str = str(uuid.uuid4())
        self._connection_map: dict = {}

    def get_connection(self, connection_type: ConnectionType):
        """Get the connection associated with the given connection type, or return None"""
        return self._connection_map.get(connection_type)

    def get_all_connections(self):
        """Get all connections held by this object"""
        return self._connection_map.values()

    def add_connection(self, connection_type: ConnectionType, connection):
        """Add a connection to the connection map, associated with the given connection type"""
        self._connection_map[connection_type] = connection

    def remove_connection(self, connection_type: ConnectionType):
        """
        Remove the connection associated with the given connection type, or raise a KeyError if
        there is no such connection
        """
        self._connection_map.pop(connection_type)

    def remove_all_connections(self):
        """Remove all connections held by this object"""
        self._connection_map = {}

    def has_connection(self, connection_type: ConnectionType):
        """Return whether this object has a connection matching the given connection type"""
        return connection_type in self._connection_map


class ConnectionService:
    """Manage a single connection, including the ability to connect/disconnect"""

    def __init__(self):
        self.connection = None
        self.owner_to_connection_map = {}
        self.owner_to_thread_map = {}
        self._service_provider = None

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(CONNECT_REQUEST, self.handle_connect_request)
        self._service_provider.server.set_request_handler(DISCONNECT_REQUEST, self.handle_disconnect_request)
        self._service_provider.server.set_request_handler(LIST_DATABASES_REQUEST, self.handle_list_databases)

    # REQUEST HANDLERS #####################################################
    def handle_connect_request(self, request_context: RequestContext, params: ConnectRequestParams) -> None:
        """Kick off a connection in response to an incoming connection request"""
        thread = threading.Thread(
            target=self._connect_and_respond,
            args=(request_context, params)
        )
        thread.daemon = True
        thread.start()
        self.owner_to_thread_map[params.owner_uri] = thread

        request_context.send_response(True)

    def handle_disconnect_request(self, request_context: RequestContext, params: DisconnectRequestParams) -> None:
        """Close a connection in response to an incoming disconnection request"""
        connection_info = self.owner_to_connection_map.get(params.owner_uri)
        if connection_info is None:
            request_context.send_response(False)
        else:
            request_context.send_response(self._close_connections(connection_info, params.type))

    def handle_list_databases(self, params: ListDatabasesParams):
        """List all databases on the server that the given URI has a connection to"""
        connection_info = self.owner_to_connection_map.get(params.owner_uri)
        if connection_info is None:
            raise RuntimeError('No connection associated with the given URI')
        if not connection_info.has_connection(ConnectionType.DEFAULT):
            self._connect(ConnectRequestParams(params.owner_uri, connection_info.details, ConnectionType.DEFAULT))
        connection = connection_info.get_connection(ConnectionType.DEFAULT)
        query_results = _execute_query(connection, 'SELECT datname FROM pg_database WHERE datistemplate = false;')
        database_names = [result[0] for result in query_results]
        return ListDatabasesResponse(database_names)

    # IMPLEMENTATION DETAILS ###############################################
    def _connect_and_respond(self, request_context: RequestContext, params: ConnectRequestParams) -> None:
        """Open a connection and fire the connection complete notification"""
        response = self._connect(params)
        request_context.send_notification(CONNECTION_COMPLETE_METHOD, response)

    def _connect(self, params: ConnectRequestParams):
        """
        Open a connection using the given connection information.

        If a connection was already open, disconnect first. Return whether the connection was
        successful
        """

        connection_info: ConnectionInfo = self.owner_to_connection_map.get(params.owner_uri)

        # If there is no saved connection or the saved connection's options do not match, create a new one
        if connection_info is None or connection_info.details.options != params.connection.options:
            if connection_info is not None:
                self._close_connections(connection_info)
            connection_info = ConnectionInfo(params.owner_uri, params.connection)
            self.owner_to_connection_map[params.owner_uri] = connection_info

        # Get the connection for the given type and build a response if it is present, otherwise open the connection
        connection = connection_info.get_connection(params.type)
        if connection is not None:
            return _build_connection_response(connection_info, params.type)

        # The connection doesn't exist yet. Build the connection string from the provided options
        connection_options = params.connection.options
        connection_string = ''
        for option, value in connection_options.items():
            key = CONNECTION_OPTION_KEY_MAP[option] if option in CONNECTION_OPTION_KEY_MAP else option
            connection_string += "{}='{}' ".format(key, value)
        logging.debug(f'Connecting with connection string {connection_string}')

        # Connect using psycopg2
        try:
            connection = psycopg2.connect(connection_string)
            connection_info.add_connection(params.type, connection)
            return _build_connection_response(connection_info, params.type)
        except Exception as err:
            return _build_connection_response_error(connection_info, params.type, err)

    @staticmethod
    def _close_connections(connection_info: ConnectionInfo, connection_type=None):
        """
        Close the connections in the given ConnectionInfo object matching the passed type, or
        close all of them if no type is given.

        Return False if no matching connections were found to close, otherwise return True.
        """
        connections_to_close = []
        if connection_type is None:
            connections_to_close = connection_info.get_all_connections()
            if not connections_to_close:
                return False
            connection_info.remove_all_connections()
        else:
            connection = connection_info.get_connection(connection_type)
            if connection is None:
                return False
            connections_to_close.append(connection)
            connection_info.remove_connection(connection_type)
        for connection in connections_to_close:
            try:
                connection.close()
            except Exception:
                # Ignore errors when disconnecting
                pass
        return True


def _build_connection_response(connection_info: ConnectionInfo, connection_type: ConnectionType):
    """Build a connection complete response object"""
    connection = connection_info.get_connection(connection_type)
    dsn_parameters = connection.get_dsn_parameters()

    connection_summary = ConnectionSummary(dsn_parameters['dbname'], dsn_parameters['host'], dsn_parameters['user'])

    response = ConnectionCompleteParams()
    response.connection_id = connection_info.connection_id
    response.connection_summary = connection_summary
    response.owner_uri = connection_info.owner_uri
    response.type = connection_type
    response.server_info = _get_server_info(connection)

    return response


def _build_connection_response_error(connection_info: ConnectionInfo, connection_type: ConnectionType, err):
    """Build a connection complete response object"""
    response: ConnectRequestParams = ConnectionCompleteParams()
    response.owner_uri = connection_info.owner_uri
    response.type = connection_type
    response.messages = repr(err)
    response.error_message = str(err)

    return response


def _get_server_info(connection):
    """Build the server info response for a connection"""
    server_version = connection.get_parameter_status('server_version')
    is_cloud = connection.get_dsn_parameters()['host'].endswith('postgres.database.azure.com')
    return ServerInfo(server_version, is_cloud)


def _execute_query(connection, query):
    """Execute a simple query without arguments for the given connection"""
    cursor = connection.cursor()
    cursor.execute(query)
    query_results = cursor.fetchall()
    cursor.commit()
    return query_results


# Dictionary mapping connection option names to their corresponding connection string keys.
# If a name is not present in this map, the name should be used as the key.
CONNECTION_OPTION_KEY_MAP = {
    'connectTimeout': 'connect_timeout',
    'clientEncoding': 'client_encoding',
    'applicationName': 'application_name'
}
