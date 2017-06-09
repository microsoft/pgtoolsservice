# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import unittest
from unittest.mock import Mock

import psycopg2

from pgsqltoolsservice.connection.contracts import (
    CONNECTION_COMPLETE_METHOD, ConnectionType, ConnectRequestParams, ConnectionDetails,
    DisconnectRequestParams, ListDatabasesParams, ListDatabasesResponse
)
from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
import tests.utils as utils


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect(self):
        """Test that the service connects to a PostgreSQL server"""
        # Set up the parameters for the connection
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'user': 'postgres',
                    'password': 'password',
                    'host': 'myserver',
                    'dbname': 'postgres'
                }
            }
        })

        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Set up the connection service and call its connect method with the supported options

        connection_service = ConnectionService()
        response = connection_service._connect(params)

        # Verify that psycopg2's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(connection_service.owner_to_connection_map[params.owner_uri].get_connection(params.type),
                      mock_connection)
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertFalse(response.server_info.is_cloud)

    def test_server_info_is_cloud(self):
        """Test that the connection response handles cloud connections correctly"""
        # Set up the parameters for the connection
        connection_uri = 'someuri'
        connection_details = ConnectionDetails()
        connection_details.options = {
            'user': 'postgres@myserver',
            'password': 'password',
            'host': 'myserver.postgres.database.azure.com',
            'dbname': 'postgres'}
        connection_type = ConnectionType.DEFAULT

        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver.postgres.database.azure.com',
            'dbname': 'postgres',
            'user': 'postgres@myserver'
        })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Set up the connection service and call its connect method with the
        # supported options
        connection_service = ConnectionService()
        response = connection_service._connect(
            ConnectRequestParams(connection_details, connection_uri, connection_type))

        # Verify that the response's serverInfo.isCloud attribute is set correctly
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertTrue(response.server_info.is_cloud)

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
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type, mock_connection)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Create a different request with the same owner uri
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': connection_uri,
            'type': connection_type,
            'connection': {
                'serverName': 'myserver',
                'databaseName': 'postgres',
                'userName': 'postgres',
                'options': {
                    'abc': 234
                }
            }
        })

        # Connect with different options, and verify that disconnect was called
        connection_service._connect(params)
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
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type, mock_connection)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Connect with identical options, and verify that disconnect was not called
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': connection_uri,
            'type': connection_type,
            'connection': {
                'serverName': 'myserver',
                'databaseName': 'postgres',
                'userName': 'postgres',
                'options': old_connection_details.options
            }
        })
        response = connection_service._connect(params)
        mock_connection.close.assert_not_called()
        psycopg2.connect.assert_not_called()
        self.assertIsNotNone(response.connection_id)

    def test_response_when_connect_fails(self):
        """Test that the proper response is given when a connection fails"""
        error_message = 'some error'
        psycopg2.connect = Mock(side_effect=Exception(error_message))
        connection_service = ConnectionService()
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'connectionString': ''
                }
            }
        })
        response = connection_service._connect(params)
        # The response should not have a connection ID and should contain the error message
        self.assertIsNone(response.connection_id)
        self.assertEqual(response.error_message, error_message)

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
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service._close_connections(old_connection_info, connection_type_1)
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
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service._close_connections(old_connection_info)
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
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = connection_service._close_connections(old_connection_info, ConnectionType.EDIT)
        mock_connection_1.close.assert_not_called()
        self.assertFalse(response)

    def test_handle_disconnect_request_unknown_uri(self):
        """Test that the handle_disconnect_request method returns false when the given URI is unknown"""
        # Setup: Create a mock request context
        rc = utils.get_mock_request_context()

        # If: I request to disconnect an unknown URI
        params: DisconnectRequestParams = DisconnectRequestParams.from_dict({
            'ownerUri': 'nonexistent'
        })
        connection_service = ConnectionService()
        connection_service.handle_disconnect_request(rc, params)

        # Then: Send result should have been called once with False
        rc.send_response.assert_called_once_with(False)
        rc.send_notification.assert_not_called()
        rc.send_error.assert_not_called()

    def test_handle_connect_request(self):
        """Test that the handle_connect_request method kicks off a new thread to do the connection"""
        # Setup: Create a mock request context to handle output
        rc = utils.get_mock_request_context()
        connection_service = ConnectionService()
        connection_service._connect = Mock(return_value=None)

        # If: I make a request to connect
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.QUERY,
            'connection': {
                'server_name': 'someserver',
                'user_name': 'someuser',
                'database_name': 'somedb',
                'options': {
                    'password': 'somepassword'
                }
            }
        })

        # Connect and wait for the thread to finish executing, then verify the connection information
        connection_service.handle_connect_request(rc, params)
        connection_thread = connection_service.owner_to_thread_map[params.owner_uri]
        self.assertIsNotNone(connection_thread)
        connection_thread.join()

        # Then:
        # ... Connect should have been called once
        connection_service._connect.assert_called_once_with(params)

        # ... A True should have been sent as the response to the request
        rc.send_response.assert_called_once_with(True)

        # ... A connection complete notification should have been sent back as well
        rc.send_notification.assert_called_once_with(CONNECTION_COMPLETE_METHOD, None)

        # ... An error should not have been called
        rc.send_error.assert_not_called()

    def test_list_databases(self):
        """Test that the list databases handler correctly lists the connection's databases"""
        # Set up the test with mock data
        mock_query_results = [('database1',), ('database2',)]
        connection_uri = 'someuri'
        connection_type = ConnectionType.DEFAULT
        mock_connection = MockConnection(
            dsn_parameters={
                'host': 'myserver',
                'dbname': 'postgres',
                'user': 'postgres'
            },
            cursor=MockCursor(mock_query_results))
        psycopg2.connect = Mock(return_value=mock_connection)
        connection_service = ConnectionService()

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Verify that calling the listdatabases handler returns the expected databases
        params = ListDatabasesParams()
        params.owner_uri = connection_uri
        response = connection_service.handle_list_databases(params)
        expected_databases = [result[0] for result in mock_query_results]
        self.assertEqual(response.database_names, expected_databases)


class MockConnection(object):
    """Class used to mock psycopg2 connection objects for testing"""

    def __init__(self, dsn_parameters=None, cursor=None):
        self.close = Mock()
        self.dsn_parameters = dsn_parameters
        self.server_version = '9.6.2'
        self.cursor = Mock(return_value=cursor)

    def get_dsn_parameters(self):
        """Mock for the connection's get_dsn_parameters method"""
        return self.dsn_parameters

    def get_parameter_status(self, parameter):
        """Mock for the connection's get_parameter_status method"""
        if parameter == 'server_version':
            return self.server_version
        else:
            raise NotImplementedError()


class MockCursor:
    """Class used to mock psycopg2 cursor objects for testing"""
    def __init__(self, query_results):
        self.execute = Mock()
        self.commit = Mock()
        self.fetchall = Mock(return_value=query_results)


if __name__ == '__main__':
    unittest.main()
