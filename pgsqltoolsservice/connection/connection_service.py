# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the connection service class, which allows for the user to connect and
disconnect and holds the current connection, if one is present"""

import threading
from typing import Dict, Optional, Tuple  # noqa
import uuid

import psycopg2
import psycopg2.extensions

from pgsqltoolsservice.connection.contracts import (
    CANCEL_CONNECT_REQUEST, CancelConnectParams,
    CONNECT_REQUEST, ConnectRequestParams,
    DISCONNECT_REQUEST, DisconnectRequestParams,
    CONNECTION_COMPLETE_METHOD, ConnectionCompleteParams,
    ConnectionDetails, ConnectionSummary, ConnectionType, ServerInfo,
    LIST_DATABASES_REQUEST, ListDatabasesParams, ListDatabasesResponse
)
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.utils.cancellation import CancellationToken


class ConnectionInfo(object):
    """Information pertaining to a unique connection instance"""

    def __init__(self, owner_uri: str, details: ConnectionDetails):
        self.owner_uri: str = owner_uri
        self.details: ConnectionDetails = details
        self.connection_id: str = str(uuid.uuid4())
        self._connection_map: Dict[ConnectionType, psycopg2.extensions.connection] = {}

    def get_connection(self, connection_type: ConnectionType) -> Optional[psycopg2.extensions.connection]:
        """Get the connection associated with the given connection type, or return None"""
        return self._connection_map.get(connection_type)

    def get_all_connections(self):
        """Get all connections held by this object"""
        return self._connection_map.values()

    def add_connection(self, connection_type: ConnectionType, connection: psycopg2.extensions.connection):
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
        self.owner_to_connection_map: Dict[str, ConnectionInfo] = {}
        self.owner_to_thread_map = {}
        self._service_provider = None
        self._cancellation_map: Dict[Tuple[str, ConnectionType], CancellationToken] = {}
        self._cancellation_lock: threading.Lock = threading.Lock()

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider

        # Register the handlers for the service
        self._service_provider.server.set_request_handler(CONNECT_REQUEST, self.handle_connect_request)
        self._service_provider.server.set_request_handler(DISCONNECT_REQUEST, self.handle_disconnect_request)
        self._service_provider.server.set_request_handler(LIST_DATABASES_REQUEST, self.handle_list_databases)
        self._service_provider.server.set_request_handler(CANCEL_CONNECT_REQUEST, self.handle_cancellation_request)

    # PUBLIC METHODS #######################################################
    def connect(self, params: ConnectRequestParams) -> Optional[ConnectionCompleteParams]:
        """
        Open a connection using the given connection information.

        If a connection was already open, disconnect first. Return a connection response indicating
        whether the connection was successful
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

        # The connection doesn't exist yet. Cancel any ongoing connection and set up a cancellation token
        cancellation_key = (params.owner_uri, params.type)
        cancellation_token = CancellationToken()
        with self._cancellation_lock:
            if cancellation_key in self._cancellation_map:
                self._cancellation_map[cancellation_key].cancel()
            self._cancellation_map[cancellation_key] = cancellation_token

        # Map the connection options to their psycopg2-specific options
        connection_options = {CONNECTION_OPTION_KEY_MAP.get(option, option): value for option, value in params.connection.options.items()}

        # Use the default database if one was not provided
        if 'dbname' not in connection_options or not connection_options['dbname']:
            connection_options['dbname'] = self._service_provider[constants.WORKSPACE_SERVICE_NAME].configuration.pgsql.default_database

        # Connect using psycopg2
        try:
            # Pass connection parameters as keyword arguments to psycopg2.connect by unpacking the connection_options dict
            connection = psycopg2.connect(**connection_options)
        except Exception as err:
            return _build_connection_response_error(connection_info, params.type, err)
        finally:
            # Remove this thread's cancellation token if needed
            with self._cancellation_lock:
                if (cancellation_key in self._cancellation_map
                        and cancellation_token is self._cancellation_map[cancellation_key]):
                    del self._cancellation_map[cancellation_key]

        # If the connection was canceled, close it
        if cancellation_token.canceled:
            connection.close()
            return None

        # Set autocommit mode so that users have control over transactions
        connection.autocommit = True

        # The connection was not canceled, so add the connection and respond
        connection_info.add_connection(params.type, connection)
        return _build_connection_response(connection_info, params.type)

    def disconnect(self, owner_uri: str, connection_type: Optional[ConnectionType]) -> bool:
        """
        Closes a single connection or all connections that belong to an owner URI based on the
        connection type provided
        :param owner_uri: URI of the connection to lookup and disconnect
        :param connection_type: The connection type to disconnect, may be omitted to close all
            connections for the owner URI
        :return: True if the connections were successfully disconnected, false otherwise
        """
        # Look up the connection to disconnect
        connection_info = self.owner_to_connection_map.get(owner_uri)
        return self._close_connections(connection_info, connection_type) if connection_info is not None else False

    def get_connection(self, owner_uri: str, connection_type: ConnectionType) -> Optional[psycopg2.extensions.connection]:
        """
        Get a psycopg2 connection for the given owner URI and connection type

        :raises ValueError: If there is no connection associated with the provided URI
        """
        connection_info = self.owner_to_connection_map.get(owner_uri)
        if connection_info is None:
            raise ValueError('No connection associated with given owner URI')

        if not connection_info.has_connection(connection_type):
            self.connect(ConnectRequestParams(connection_info.details, owner_uri, connection_type))
        return connection_info.get_connection(connection_type)

    def get_connection_info(self, owner_uri: str) -> ConnectionInfo:
        """Get the ConnectionInfo object for the given owner URI, or None if there is no connection"""
        return self.owner_to_connection_map.get(owner_uri)

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
        request_context.send_response(self.disconnect(params.owner_uri, params.type))

    def handle_list_databases(self, request_context: RequestContext, params: ListDatabasesParams):
        """List all databases on the server that the given URI has a connection to"""
        connection = None
        try:
            connection = self.get_connection(params.owner_uri, ConnectionType.DEFAULT)
        except ValueError as err:
            request_context.send_error(str(err))
            return
        query_results = None
        try:
            query_results = _execute_query(connection, 'SELECT datname FROM pg_database WHERE datistemplate = false;')
        except psycopg2.ProgrammingError as err:
            if self._service_provider is not None and self._service_provider.logger is not None:
                self._service_provider.logger.exception('Error listing databases')
            request_context.send_error(str(err))
            return
        database_names = [result[0] for result in query_results]
        request_context.send_response(ListDatabasesResponse(database_names))

    def handle_cancellation_request(self, request_context: RequestContext, params: CancelConnectParams) -> None:
        """Cancel a connection attempt in response to a cancellation request"""
        cancellation_key = (params.owner_uri, params.type)
        with self._cancellation_lock:
            connection_found = cancellation_key in self._cancellation_map
            if connection_found:
                self._cancellation_map[cancellation_key].cancel()
        request_context.send_response(connection_found)

    # IMPLEMENTATION DETAILS ###############################################
    def _connect_and_respond(self, request_context: RequestContext, params: ConnectRequestParams) -> None:
        """Open a connection and fire the connection complete notification"""
        response = self.connect(params)

        # Send the connection complete response unless the connection was canceled
        if response is not None:
            request_context.send_notification(CONNECTION_COMPLETE_METHOD, response)

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


def _build_connection_response(connection_info: ConnectionInfo, connection_type: ConnectionType) -> ConnectionCompleteParams:
    """Build a connection complete response object"""
    connection = connection_info.get_connection(connection_type)
    dsn_parameters = connection.get_dsn_parameters()

    connection_summary = ConnectionSummary(
        server_name=dsn_parameters['host'],
        database_name=dsn_parameters['dbname'],
        user_name=dsn_parameters['user'])

    response: ConnectionCompleteParams = ConnectionCompleteParams()
    response.connection_id = connection_info.connection_id
    response.connection_summary = connection_summary
    response.owner_uri = connection_info.owner_uri
    response.type = connection_type
    response.server_info = _get_server_info(connection)

    return response


def _build_connection_response_error(connection_info: ConnectionInfo, connection_type: ConnectionType, err)\
        -> ConnectionCompleteParams:
    """Build a connection complete response object"""
    response: ConnectionCompleteParams = ConnectionCompleteParams()
    response.owner_uri = connection_info.owner_uri
    response.type = connection_type
    response.messages = str(err)
    response.error_message = str(err)

    return response


def _get_server_info(connection):
    """Build the server info response for a connection"""
    server_version = connection.get_parameter_status('server_version')
    host = connection.get_dsn_parameters()['host']
    is_cloud = host.endswith('database.azure.com') or host.endswith('database.windows.net')
    return ServerInfo(server_version, is_cloud)


def _execute_query(connection, query):
    """
    Execute a simple query without arguments for the given connection

    :raises psycopg2.ProgrammingError: if there was no result set when executing the query
    """
    cursor = connection.cursor()
    cursor.execute(query)
    try:
        query_results = cursor.fetchall()
    except psycopg2.ProgrammingError:
        raise
    return query_results


# Dictionary mapping connection option names to their corresponding connection string keys.
# If a name is not present in this map, the name should be used as the key.
CONNECTION_OPTION_KEY_MAP = {
    'connectTimeout': 'connect_timeout',
    'clientEncoding': 'client_encoding',
    'applicationName': 'application_name'
}
