# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import mock
import unittest

import psycopg2

from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import (
    ConnectRequestParams,
    DisconnectRequestParams,
    ConnectionType
)
from pgsqltoolsservice.hosting import RequestContext


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect_with_connection_options(self):
        """Test that the service connects and disconnects to/from a PostgreSQL server"""
        self.connect_internal(ConnectionInfo(
            None,
            {'options': {
                'user': 'postgres',
                'password': 'password',
                'host': 'myserver',
                'dbname': 'postgres'
            }},
            None))

    def connect_internal(self, connection_info):
        """Helper method for testing connections"""
        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })
        psycopg2.connect = mock.Mock(return_value=mock_connection)
        # Set up the connection service and call its connect method with the supported options
        connection_service = ConnectionService()
        response = connection_service._connect(connection_info)
        # Verify that psycopg2's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(connection_service.connection, mock_connection)
        self.assertIsNotNone(response.connection_id)

    def test_connect_disconnects_existing_connection(self):
        """Test that the connect method disconnects an existing connection if one exists"""
        old_mock_connection = MockConnection()
        new_mock_connection = MockConnection()
        connection_service = ConnectionService()
        connection_service.connection = old_mock_connection
        psycopg2.connect = mock.Mock(return_value=new_mock_connection)
        connection_service._connect(ConnectionInfo(None, {'options': {'connectionString': ''}}, None))
        old_mock_connection.close.assert_called_once()

    def test_response_when_connect_fails(self):
        """Test that the proper response is given when a connection fails"""
        error_message = 'some error'
        psycopg2.connect = mock.Mock(side_effect=Exception(error_message))
        connection_service = ConnectionService()
        response = connection_service._connect(ConnectionInfo(None, {'options': {'connectionString': ''}}, None))
        # The response should not have a connection ID and should contain the error message
        self.assertIsNone(response.connection_id)
        self.assertEqual(response.error_message, error_message)

    def test_disconnect(self):
        """Test that the disconnect method calls close on the open connection"""
        mock_connection = MockConnection()
        connection_service = ConnectionService()
        connection_service.connection = mock_connection
        connection_service._disconnect()
        mock_connection.close.assert_called_once()

    def test_handle_connect_request(self):
        """Test that the handle_connect_request method kicks off a new thread to do the connection"""
        # Setup:
        # ... Create a connection service with a mocked up connect
        connection_service = ConnectionService()
        connect_mock = mock.MagicMock()
        connection_service._connect = connect_mock

        # ... Create a request context with mocked out send_response and send_notification
        send_notification_mock = mock.MagicMock()
        send_response_mock = mock.MagicMock()
        rc = RequestContext(None, None)
        rc.send_notification = send_notification_mock
        rc.send_response = send_response_mock

        # If:
        # ... I submit a request to connect
        params = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.QUERY,
            'connection': {
                'server': 'someServer',
                'user': 'someUser',
                'password': 'somePassword'
            }
        })
        connection_service.handle_connect_request(rc, params)

        # ... Wait for connection execution to complete
        connection_thread = connection_service._connection_thread
        self.assertIsNotNone(connection_thread)
        connection_thread.join()

        # Then:
        # ... The connect method should have been called once with the provided params
        connect_mock.assert_called_once()

        # ... The send result should have been called once
        send_response_mock.assert_called_once_with(True)

        # ... The send event should have been called once, as well
        send_notification_mock.assert_called_once()

    def test_handle_disconnect_request(self):
        """Test that the handle_disconnect_request method calls disconnect for the open connection"""
        # Setup:
        # ... Create connection service with mocked out connection
        connection_service = ConnectionService()
        connection = MockConnection()
        connection_service.connection = connection

        # ... Create request context with mocked out send_response
        rc = RequestContext(None, None)
        send_response_mock = mock.MagicMock()
        rc.send_response = send_response_mock

        # If: I handle a disconnect request
        params = DisconnectRequestParams.from_dict({'ownerUri': 'someUri'})
        connection_service.handle_disconnect_request(rc, params)

        # Then:
        # ... The connection should have been closed
        connection.close.assert_called_once()

        # ... The response should have been sent
        send_response_mock.assert_called_once_with(True)

    def test_handle_disconnect_request_fails(self):
        """Test that the handle_disconnect_request method returns false when failing"""
        # Setup:
        # ... Create connection service with mocked out connection that fails on close
        connection_service = ConnectionService()
        connection = MockConnection()
        connection.close = mock.Mock(side_effect=Exception())
        connection_service.connection = connection

        # ... Create request context with mocked out send_response
        rc = RequestContext(None, None)
        send_response_mock = mock.MagicMock()
        rc.send_response = send_response_mock

        # If: I handle a disconnect request
        params = DisconnectRequestParams.from_dict({'ownerUri': 'someUri'})
        connection_service.handle_disconnect_request(rc, params)

        # Then: A response should have been send
        send_response_mock.assert_called_once_with(False)


class MockConnection(object):
    """Class used to mock psycopg2 connection objects for testing"""

    def __init__(self, dsn_parameters=None):
        self.close = mock.Mock()
        self.dsn_parameters = dsn_parameters

    def get_dsn_parameters(self):
        """Mock for the connection's get_dsn_parameters method"""
        return self.dsn_parameters


if __name__ == '__main__':
    unittest.main()
