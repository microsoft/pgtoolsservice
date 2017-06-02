# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import unittest
from unittest.mock import Mock

import psycopg2

from pgsqltoolsservice.connection.contracts import CONNECTION_COMPLETE_NOTIFICATION_TYPE, ConnectionType
from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.server import Server


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect(self):
        """Test that the service connects to a PostgreSQL server"""
        # Set up the parameters for the connection
        connection_uri = 'someuri'
        connection_details = {'options': {
            'user': 'postgres',
            'password': 'password',
            'host': 'myserver',
            'dbname': 'postgres'}}
        connection_type = ConnectionType.DEFAULT

        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Set up the connection service and call its connect method with the supported options
        connection_service = ConnectionService(None)
        response = connection_service.connect(connection_uri, connection_details, connection_type)

        # Verify that psycopg2's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(connection_service.owner_to_connection_map[connection_uri].get_connection(connection_type),
                      mock_connection)
        self.assertIsNotNone(response.connectionId)

    def test_changing_options_disconnects_existing_connection(self):
        """
        Test that the connect method disconnects an existing connection when trying to open the same connection with
        different options
        """
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type = ConnectionType.DEFAULT
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })
        psycopg2.connect = Mock(return_value=mock_connection)
        connection_service = ConnectionService(None)

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_info = ConnectionInfo(connection_uri, {'options': {'abc': 123}})
        old_connection_info.add_connection(connection_type, mock_connection)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Connect with different options, and verify that disconnect was called
        connection_service.connect(connection_uri, {'options': {'abc': 234}}, connection_type)
        mock_connection.close.assert_called_once()

    def test_same_options_uses_existing_connection(self):
        """Test that the connect method uses an existing connection when connecting again with the same options"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type = ConnectionType.DEFAULT
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })
        psycopg2.connect = Mock(return_value=mock_connection)
        connection_service = ConnectionService(None)

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_info = ConnectionInfo(connection_uri, {'options': {'abc': 123}})
        old_connection_info.add_connection(connection_type, mock_connection)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Connect with different options, and verify that disconnect was called
        response = connection_service.connect(connection_uri, {'options': {'abc': 123}}, connection_type)
        mock_connection.close.assert_not_called()
        psycopg2.connect.assert_not_called()
        self.assertIsNotNone(response.connectionId)

    def test_response_when_connect_fails(self):
        """Test that the proper response is given when a connection fails"""
        error_message = 'some error'
        psycopg2.connect = Mock(side_effect=Exception(error_message))
        connection_service = ConnectionService(None)
        response = connection_service.connect(None, {'options': {'connectionString': ''}}, None)
        # The response should not have a connection ID and should contain the error message
        self.assertIsNone(response.connectionId)
        self.assertEqual(response.errorMessage, error_message)

    def test_disconnect_single_type(self):
        """Test that the disconnect method calls close on a single open connection type when a type is given"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type_1 = ConnectionType.DEFAULT
        connection_type_2 = ConnectionType.EDIT
        mock_connection_1 = MockConnection(dsn_parameters={
            'host': 'myserver1',
            'dbname': 'postgres1',
            'user': 'postgres1'
        })
        mock_connection_2 = MockConnection(dsn_parameters={
            'host': 'myserver2',
            'dbname': 'postgres2',
            'user': 'postgres2'
        })
        connection_service = ConnectionService(None)

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_info = ConnectionInfo(connection_uri, {'options': {'abc': 123}})
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service.handle_disconnect_request(connection_uri, connection_type_1)
        mock_connection_1.close.assert_called_once()
        mock_connection_2.close.assert_not_called()
        self.assertTrue(response)

    def test_disconnect_all_types(self):
        """Test that the disconnect method calls close on a all open connection types when no type is given"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type_1 = ConnectionType.DEFAULT
        connection_type_2 = ConnectionType.EDIT
        mock_connection_1 = MockConnection(dsn_parameters={
            'host': 'myserver1',
            'dbname': 'postgres1',
            'user': 'postgres1'
        })
        mock_connection_2 = MockConnection(dsn_parameters={
            'host': 'myserver2',
            'dbname': 'postgres2',
            'user': 'postgres2'
        })
        connection_service = ConnectionService(None)

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_info = ConnectionInfo(connection_uri, {'options': {'abc': 123}})
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service.handle_disconnect_request(connection_uri)
        mock_connection_1.close.assert_called_once()
        mock_connection_2.close.assert_called_once()
        self.assertTrue(response)

    def test_disconnect_for_invalid_connection(self):
        """Test that the disconnect method returns false when called on a connection that does not exist"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type_1 = ConnectionType.DEFAULT
        mock_connection_1 = MockConnection(dsn_parameters={
            'host': 'myserver1',
            'dbname': 'postgres1',
            'user': 'postgres1'
        })
        connection_service = ConnectionService(None)

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_info = ConnectionInfo(connection_uri, {'options': {'abc': 123}})
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service.handle_disconnect_request(connection_uri, ConnectionType.EDIT)
        mock_connection_1.close.assert_not_called()
        self.assertFalse(response)

    def test_handle_disconnect_request_unknown_uri(self):
        """Test that the handle_disconnect_request method returns false when the given URI is unknown"""
        connection_service = ConnectionService(None)
        result = connection_service.handle_disconnect_request('someuri')
        self.assertFalse(result)

    def test_handle_connect_request(self):
        """Test that the handle_connect_request method kicks off a new thread to do the connection"""
        # Set up the test with mock servers and methods
        output_dict = {}

        def mock_register_thread(thread):
            """Mock register_thread method to be used for the server"""
            output_dict['connection_thread'] = thread

        mock_server = Server(None, None)
        mock_server.register_thread = mock_register_thread
        mock_server.send_event = Mock()
        connection_service = ConnectionService(mock_server)
        connection_service.connect = Mock(return_value=None)

        # Set up the connection request
        owner_uri = 'someuri'
        connection_type = ConnectionType.QUERY
        connection_details = {'server': 'someserver', 'user': 'someuser', 'password': 'somepassword'}

        # Connect and wait for the thread to finish executing, then verify the connection information
        connection_service.handle_connect_request(owner_uri, connection_details, connection_type)
        connection_thread = output_dict['connection_thread']
        self.assertIsNotNone(connection_thread)
        connection_thread.join()
        connection_service.connect.assert_called_once_with(owner_uri, connection_details, connection_type)

        # Verify that a connection complete notification was sent
        mock_server.send_event.assert_called_once_with(CONNECTION_COMPLETE_NOTIFICATION_TYPE, None)


class MockConnection(object):
    """Class used to mock psycopg2 connection objects for testing"""

    def __init__(self, dsn_parameters=None):
        self.close = Mock()
        self.dsn_parameters = dsn_parameters

    def get_dsn_parameters(self):
        """Mock for the connection's get_dsn_parameters method"""
        return self.dsn_parameters


if __name__ == '__main__':
    unittest.main()
