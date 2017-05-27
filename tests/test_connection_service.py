# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection_service.py"""

from __future__ import unicode_literals
import unittest

import mock
import psycopg2

from pgsqltoolsservice.connection_service import ConnectionInfo, ConnectionService
from pgsqltoolsservice.contracts.connection import CONNECTION_COMPLETE_NOTIFICATION_TYPE, ConnectionType
from pgsqltoolsservice.server import Server


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
        connection_service = ConnectionService(None)
        response = connection_service.connect(connection_info)
        # Verify that psycopg2's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(connection_service.connection, mock_connection)
        self.assertIsNotNone(response.connectionId)

    def test_connect_disconnects_existing_connection(self):
        """Test that the connect method disconnects an existing connection if one exists"""
        old_mock_connection = MockConnection()
        new_mock_connection = MockConnection()
        connection_service = ConnectionService(None)
        connection_service.connection = old_mock_connection
        psycopg2.connect = mock.Mock(return_value=new_mock_connection)
        connection_service.connect(ConnectionInfo(None, {'options': {'connectionString': ''}}, None))
        old_mock_connection.close.assert_called_once()

    def test_response_when_connect_fails(self):
        """Test that the proper response is given when a connection fails"""
        error_message = 'some error'
        psycopg2.connect = mock.Mock(side_effect=Exception(error_message))
        connection_service = ConnectionService(None)
        response = connection_service.connect(ConnectionInfo(None, {'options': {'connectionString': ''}}, None))
        # The response should not have a connection ID and should contain the error message
        self.assertIsNone(response.connectionId)
        self.assertEqual(response.errorMessage, error_message)

    def test_disconnect(self):
        """Test that the disconnect method calls close on the open connection"""
        mock_connection = MockConnection()
        connection_service = ConnectionService(None)
        connection_service.connection = mock_connection
        connection_service.disconnect()
        mock_connection.close.assert_called_once()

    def test_handle_connect_request(self):
        """Test that the handle_connect_request method kicks off a new thread to do the connection"""
        # Set up the test with mock servers and methods
        output_dict = {}

        def mock_register_thread(thread):
            """Mock register_thread method to be used for the server"""
            output_dict['connection_thread'] = thread

        def mock_connect(info):
            """Mock connect method in order to prevent the service from actually trying to connect"""
            output_dict['connection_info'] = info

        mock_server = Server(None, None)
        mock_server.register_thread = mock_register_thread
        mock_server.send_event = mock.Mock()
        connection_service = ConnectionService(mock_server)
        connection_service.connect = mock_connect

        # Set up the connection request
        owner_uri = 'someuri'
        connection_type = ConnectionType.QUERY
        connection_details = {'server': 'someserver', 'user': 'someuser', 'password': 'somepassword'}

        # Connect and wait for the thread to finish executing, then verify the connection information
        connection_service.handle_connect_request(owner_uri, connection_details, connection_type)
        connection_thread = output_dict['connection_thread']
        self.assertIsNotNone(connection_thread)
        connection_thread.join()
        connection_info = output_dict['connection_info']
        self.assertIsNotNone(connection_info)
        self.assertEqual(connection_info.owner_uri, owner_uri)
        self.assertEqual(connection_info.details, connection_details)
        self.assertEqual(connection_info.connection_type, connection_type)

        # Verify that a connection complete notification was sent
        mock_server.send_event.assert_called_once_with(CONNECTION_COMPLETE_NOTIFICATION_TYPE, None)

    def test_handle_disconnect_request(self):
        """Test that the handle_disconnect_request method calls disconnect for the open connection"""
        connection_service = ConnectionService(None)
        connection = MockConnection()
        connection_service.connection = connection
        result = connection_service.handle_disconnect_request('someuri')
        connection.close.assert_called_once()
        self.assertTrue(result)

    def test_handle_disconnect_request_fails(self):
        """Test that the handle_disconnect_request method returns false when failing"""
        connection_service = ConnectionService(None)
        connection = MockConnection()
        connection.close = mock.Mock(side_effect=Exception())
        connection_service.connection = connection
        result = connection_service.handle_disconnect_request('someuri')
        self.assertFalse(result)


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
