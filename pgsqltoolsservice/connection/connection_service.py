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

from pgsqltoolsservice.connection.contracts.contract_impl import (
    CONNECTION_COMPLETE_NOTIFICATION_TYPE,
    ConnectionCompleteParams,
    ConnectionSummary,
    ConnectionType
)


class ConnectionService(object):
    """Manage a single connection, including the ability to connect/disconnect"""

    def __init__(self, server):
        self.connection = None
        self.server = server

    def handle_connect_request(self, ownerUri, connection, type=ConnectionType.DEFAULT):
        """Kick off a connection in response to an incoming connection request"""
        connection_info = ConnectionInfo(ownerUri, connection, type)
        thread = threading.Thread(target=self.connect_and_respond, args=(connection_info,))
        self.server.register_thread(thread)
        thread.daemon = True
        thread.start()
        return True

    def handle_disconnect_request(self, ownerUri, type=None):
        """Close a connection in response to an incoming disconnection request"""
        return self.disconnect()

    def connect_and_respond(self, connection_info):
        """Open a connection and fire the connection complete notification"""
        response = self.connect(connection_info)
        self.server.send_event(CONNECTION_COMPLETE_NOTIFICATION_TYPE, response)

    def connect(self, connection_info):
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
            self.disconnect()
        try:
            self.connection = psycopg2.connect(connection_string)
            return build_connection_response(connection_info, self.connection)
        except Exception as err:
            return build_connection_response_error(connection_info, err)

    def disconnect(self):
        """Close a connection, if there is currently one open"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                return False
            self.connection = None
        return True


class ConnectionInfo(object):
    """Information pertaining to a unique connection instance"""

    def __init__(self, owner_uri, details, connection_type):
        self.owner_uri = owner_uri
        self.details = details
        self.connection_id = str(uuid.uuid4())
        self.connection_type = connection_type


def build_connection_response(connection_info, connection):
    """Build a connection complete response object"""
    response = ConnectionCompleteParams(
        ownerUri=connection_info.owner_uri,
        type=connection_info.connection_type,
        connectionId=connection_info.connection_id
    )
    dsn_parameters = connection.get_dsn_parameters()
    response.connectionSummary = ConnectionSummary(
        serverName=dsn_parameters['host'],
        databaseName=dsn_parameters['dbname'],
        userName=dsn_parameters['user']
    )
    return response


def build_connection_response_error(connection_info, err):
    """Build a connection complete response object"""
    response = ConnectionCompleteParams(
        ownerUri=connection_info.owner_uri,
        type=connection_info.connection_type,
        messages=repr(err),
        errorMessage=str(err)
    )
    return response


# Dictionary mapping connection option names to their corresponding connection string keys.
# If a name is not present in this map, the name should be used as the key.
CONNECTION_OPTION_KEY_MAP = {
    'connectTimeout': 'connect_timeout',
    'clientEncoding': 'client_encoding',
    'applicationName': 'application_name'
}
