# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the connection service class, which allows for the user to connect and
disconnect and holds the current connection, if one is present"""

from __future__ import unicode_literals
import logging
import threading
import uuid

import psycopg2

from pgsqltoolsservice.connection.contracts import (
    connect_request, ConnectRequestParams,
    disconnect_request, DisconnectRequestParams,
    connection_complete_method, ConnectionCompleteParams,
    ConnectionSummary
)
from pgsqltoolsservice.hosting import RequestContext, ServiceProvider


class ConnectionInfo(object):
    """Information pertaining to a unique connection instance"""

    def __init__(self, owner_uri, details, connection_type):
        self.owner_uri = owner_uri
        self.details = details
        self.connection_id = str(uuid.uuid4())
        self.connection_type = connection_type


class ConnectionService:
    """Manage a single connection, including the ability to connect/disconnect"""

    def __init__(self, service_provider: [ServiceProvider, None]):
        self.connection = None
        self._service_provider = service_provider

    def initialize(self):
        # Register the handlers for the service
        self._service_provider.server.set_request_handler(connect_request, self.handle_connect_request)
        self._service_provider.server.set_request_handler(disconnect_request, self.handle_disconnect_request)

    # REQUEST HANDLERS #####################################################
    def handle_connect_request(self, request_context: RequestContext, params: ConnectRequestParams) -> None:
        """Kick off a connection in response to an incoming connection request"""
        connection_info = ConnectionInfo(params.owner_uri, params.connection, params.type)
        thread = threading.Thread(target=self._connect_and_respond, args=(connection_info, request_context))
        thread.daemon = True
        thread.start()
        request_context.send_response(True)

    def handle_disconnect_request(self, request_context: RequestContext, params: DisconnectRequestParams) -> None:
        """Close a connection in response to an incoming disconnection request"""
        request_context.send_response(self._disconnect())

    # IMPLEMENTATION DETAILS ###############################################
    def _connect_and_respond(self, connection_info: ConnectionInfo, request_context: RequestContext) -> None:
        """Open a connection and fire the connection complete notification"""
        response = self._connect(connection_info)
        request_context.send_notification(connection_complete_method, response)

    def _connect(self, connection_info):
        """
        Open a connection using the given connection information.

        If a connection was already open, disconnect first. Return whether the connection was
        successful
        """

        # Build the connection string from the provided options
        connection_options = connection_info.details['options']
        connection_string = ''
        for option, value in connection_options.items():
            key = CONNECTION_OPTION_KEY_MAP[option] if option in CONNECTION_OPTION_KEY_MAP else option
            connection_string += "{}='{}' ".format(key, value)
        logging.debug(f'Connecting with connection string {connection_string}')

        # Connect using psycopg2
        if self.connection:
            self._disconnect()
        try:
            self.connection = psycopg2.connect(connection_string)
            return build_connection_response(connection_info, self.connection)
        except Exception as err:
            return build_connection_response_error(connection_info, err)

    def _disconnect(self):
        """Close a connection, if there is currently one open"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                return False
            self.connection = None
        return True


def build_connection_response(connection_info, connection):
    """Build a connection complete response object"""
    dsn_parameters = connection.get_dsn_parameters()

    connection_summary = ConnectionSummary()
    connection_summary.database_name = dsn_parameters['dbname']
    connection_summary.server_name = dsn_parameters['host']
    connection_summary.user_name = dsn_parameters['user']

    response = ConnectionCompleteParams()
    response.connection_id = connection_info.connection_id
    response.connection_summary = connection_summary
    response.owner_uri = connection_info.owner_uri
    response.type = connection_info.connection_type

    return response


def build_connection_response_error(connection_info, err):
    """Build a connection complete response object"""
    response = ConnectionCompleteParams()
    response.owner_uri = connection_info.owner_uri
    response.type = connection_info.connection_type
    response.messages = repr(err)
    response.error_message = str(err)

    return response


# Dictionary mapping connection option names to their corresponding connection string keys.
# If a name is not present in this map, the name should be used as the key.
CONNECTION_OPTION_KEY_MAP = {
    'connectTimeout': 'connect_timeout',
    'clientEncoding': 'client_encoding',
    'applicationName': 'application_name'
}
