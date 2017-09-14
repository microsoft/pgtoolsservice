# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock

import psycopg2

from pgsqltoolsservice.connection.contracts import (
    CONNECTION_COMPLETE_METHOD, ConnectionType, ConnectRequestParams, ConnectionDetails,
    DisconnectRequestParams, ListDatabasesParams, ConnectionCompleteParams, CancelConnectParams
)
from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
import pgsqltoolsservice.connection.connection_service
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.utils.cancellation import CancellationToken
from pgsqltoolsservice.workspace import WorkspaceService
import tests.utils as utils
from tests.utils import MockConnection, MockCursor


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def setUp(self):
        """Set up the tests with a connection service"""
        self.connection_service = ConnectionService()
        self.connection_service._service_provider = utils.get_mock_service_provider({constants.WORKSPACE_SERVICE_NAME: WorkspaceService()})

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

        response = self.connection_service.connect(params)

        # Verify that psycopg2's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(self.connection_service.owner_to_connection_map[params.owner_uri].get_connection(params.type),
                      mock_connection)
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertFalse(response.server_info.is_cloud)

    def test_server_info_is_cloud(self):
        """Test that the connection response handles cloud connections correctly"""
        self.server_info_is_cloud_internal('postgres.database.azure.com', True)
        self.server_info_is_cloud_internal('postgres.database.windows.net', True)
        self.server_info_is_cloud_internal('some.host.com', False)

    def server_info_is_cloud_internal(self, host_suffix, is_cloud):
        """Test that the connection response handles cloud connections correctly"""
        # Set up the parameters for the connection
        connection_uri = 'someuri'
        connection_details = ConnectionDetails()
        connection_details.options = {
            'user': 'postgres@myserver',
            'password': 'password',
            'host': f'myserver{host_suffix}',
            'dbname': 'postgres'}
        connection_type = ConnectionType.DEFAULT

        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': f'myserver{host_suffix}',
            'dbname': 'postgres',
            'user': 'postgres@myserver'
        })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Set up the connection service and call its connect method with the
        # supported options
        response = self.connection_service.connect(
            ConnectRequestParams(connection_details, connection_uri, connection_type))

        # Verify that the response's serverInfo.isCloud attribute is set correctly
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertEqual(response.server_info.is_cloud, is_cloud)

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

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data({
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres',
            'abc': 123
        })
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type, mock_connection)
        self.connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Create a different request with the same owner uri
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': connection_uri,
            'type': connection_type,
            'connection': {
                'options': {
                    'host': 'myserver',
                    'dbname': 'postgres',
                    'user': 'postgres',
                    'abc': 234
                }
            }
        })

        # Connect with different options, and verify that disconnect was called
        self.connection_service.connect(params)
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

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data({
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres',
            'abc': 123
        })
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type, mock_connection)
        self.connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Connect with identical options, and verify that disconnect was not called
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': connection_uri,
            'type': connection_type,
            'connection': {
                'options': old_connection_details.options
            }
        })
        response = self.connection_service.connect(params)
        mock_connection.close.assert_not_called()
        psycopg2.connect.assert_not_called()
        self.assertIsNotNone(response.connection_id)

    def test_response_when_connect_fails(self):
        """Test that the proper response is given when a connection fails"""
        error_message = 'some error'
        psycopg2.connect = Mock(side_effect=Exception(error_message))
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'connectionString': ''
                }
            }
        })
        response = self.connection_service.connect(params)
        # The response should not have a connection ID and should contain the error message
        self.assertIsNone(response.connection_id)
        self.assertEqual(response.error_message, error_message)

    def test_register_on_connect_callback(self):
        """Tests that callbacks are added to a list of callbacks as expected"""
        callback = MagicMock()
        self.connection_service.register_on_connect_callback(callback)
        self.assertListEqual(self.connection_service._on_connect_callbacks, [callback])

    def test_on_connect_backs_called_on_connect(self):
        self.run_on_connect_callback(ConnectionType.DEFAULT, True)
        self.run_on_connect_callback(ConnectionType.EDIT, False)
        self.run_on_connect_callback(ConnectionType.INTELLISENSE, False)
        self.run_on_connect_callback(ConnectionType.QUERY, False)

    def run_on_connect_callback(self, conn_type: ConnectionType, expect_callback: bool) -> None:
        """Inner function for callback tests that verifies expected behavior given different connection types"""
        callbacks = [MagicMock(), MagicMock()]
        for callback in callbacks:
            self.connection_service.register_on_connect_callback(callback)

        # Set up the parameters for the connection
        connection_uri = 'someuri'
        connection_details = ConnectionDetails()
        connection_details.options = {
            'user': 'postgres@myserver',
            'password': 'password',
            'host': f'myserver',
            'dbname': 'postgres'}
        connection_type = conn_type

        # Set up the mock connection for psycopg2's connect method to return
        mock_connection = MockConnection(dsn_parameters={
            'host': f'myserver',
            'dbname': 'postgres',
            'user': 'postgres@myserver'
        })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Set up the connection service and call its connect method with the
        # supported options
        self.connection_service.connect(
            ConnectRequestParams(connection_details, connection_uri, connection_type))
        self.connection_service.get_connection(connection_uri, conn_type)
        # ... The mock config change callbacks should have been called
        for callback in callbacks:
            if (expect_callback):
                callback.assert_called_once()
                # Verify call args match expected
                callargs: ConnectionInfo = callback.call_args[0][0]
                self.assertEqual(callargs.owner_uri, connection_uri)
            else:
                callback.assert_not_called()

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

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data({'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        self.connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = self.connection_service._close_connections(old_connection_info, connection_type_1)
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

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data({'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        old_connection_info.add_connection(connection_type_2, mock_connection_2)
        self.connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = self.connection_service._close_connections(old_connection_info)
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

        # Insert a ConnectionInfo object into the connection service's map
        old_connection_details = ConnectionDetails.from_data({'abc': 123})
        old_connection_info = ConnectionInfo(connection_uri, old_connection_details)
        old_connection_info.add_connection(connection_type_1, mock_connection_1)
        self.connection_service.owner_to_connection_map[connection_uri] = old_connection_info

        # Close the connection by calling disconnect
        response = self.connection_service._close_connections(old_connection_info, ConnectionType.EDIT)
        mock_connection_1.close.assert_not_called()
        self.assertFalse(response)

    def test_handle_disconnect_request_unknown_uri(self):
        """Test that the handle_disconnect_request method returns false when the given URI is unknown"""
        # Setup: Create a mock request context
        rc = utils.MockRequestContext()

        # If: I request to disconnect an unknown URI
        params: DisconnectRequestParams = DisconnectRequestParams.from_dict({
            'ownerUri': 'nonexistent'
        })
        self.connection_service.handle_disconnect_request(rc, params)

        # Then: Send result should have been called once with False
        rc.send_response.assert_called_once_with(False)
        rc.send_notification.assert_not_called()
        rc.send_error.assert_not_called()

    def test_handle_connect_request(self):
        """Test that the handle_connect_request method kicks off a new thread to do the connection"""
        # Setup: Create a mock request context to handle output
        rc = utils.MockRequestContext()
        connect_response = ConnectionCompleteParams()
        self.connection_service.connect = Mock(return_value=connect_response)

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
        self.connection_service.handle_connect_request(rc, params)
        connection_thread = self.connection_service.owner_to_thread_map[params.owner_uri]
        self.assertIsNotNone(connection_thread)
        connection_thread.join()

        # Then:
        # ... Connect should have been called once
        self.connection_service.connect.assert_called_once_with(params)

        # ... A True should have been sent as the response to the request
        rc.send_response.assert_called_once_with(True)

        # ... A connection complete notification should have been sent back as well
        rc.send_notification.assert_called_once_with(CONNECTION_COMPLETE_METHOD, connect_response)

        # ... An error should not have been called
        rc.send_error.assert_not_called()

    def test_list_databases(self):
        """Test that the list databases handler correctly lists the connection's databases"""
        # Set up the test with mock data
        mock_query_results = [('database1',), ('database2',)]
        connection_uri = 'someuri'
        mock_connection = MockConnection(
            dsn_parameters={
                'host': 'myserver',
                'dbname': 'postgres',
                'user': 'postgres'
            },
            cursor=MockCursor(mock_query_results))
        psycopg2.connect = Mock(return_value=mock_connection)
        mock_request_context = utils.MockRequestContext()

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data({})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        self.connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Verify that calling the listdatabases handler returns the expected databases
        params = ListDatabasesParams()
        params.owner_uri = connection_uri

        self.connection_service.handle_list_databases(mock_request_context, params)
        expected_databases = [result[0] for result in mock_query_results]
        self.assertEqual(mock_request_context.last_response_params.database_names, expected_databases)

    def test_get_connection_for_existing_connection(self):
        """Test that get_connection returns a connection that already exists for the given URI and type"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type = ConnectionType.EDIT
        mock_connection = MockConnection(
            dsn_parameters={
                'host': 'myserver',
                'dbname': 'postgres',
                'user': 'postgres'
            })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data({})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        self.connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Get the connection without first creating it
        connection = self.connection_service.get_connection(connection_uri, connection_type)
        self.assertEqual(connection, mock_connection)
        psycopg2.connect.assert_called_once()

    def test_get_connection_creates_connection(self):
        """Test that get_connection creates a new connection when none exists for the given URI and type"""
        # Set up the test with mock data
        connection_uri = 'someuri'
        connection_type = ConnectionType.EDIT
        mock_connection = MockConnection(
            dsn_parameters={
                'host': 'myserver',
                'dbname': 'postgres',
                'user': 'postgres'
            })
        psycopg2.connect = Mock(return_value=mock_connection)

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data({})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        self.connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Open the connection
        self.connection_service.connect(ConnectRequestParams(connection_details, connection_uri, connection_type))

        # Get the connection
        connection = self.connection_service.get_connection(connection_uri, connection_type)
        self.assertEqual(connection, mock_connection)
        psycopg2.connect.assert_called_once()

    def test_get_connection_for_invalid_uri(self):
        """Test that get_connection raises an error if the given URI is unknown"""
        with self.assertRaises(ValueError):
            self.connection_service.get_connection('someuri', ConnectionType.DEFAULT)

    def test_list_databases_handles_invalid_uri(self):
        """Test that the connection/listdatabases handler returns an error when the given URI is unknown"""
        mock_request_context = utils.MockRequestContext()
        params = ListDatabasesParams()
        params.owner_uri = 'unknown_uri'

        self.connection_service.handle_list_databases(mock_request_context, params)
        self.assertIsNone(mock_request_context.last_notification_method)
        self.assertIsNone(mock_request_context.last_notification_params)
        self.assertIsNone(mock_request_context.last_response_params)
        self.assertIsNotNone(mock_request_context.last_error_message)

    def test_list_databases_handles_query_failure(self):
        """Test that the list databases handler returns an error if the list databases query fails for any reason"""
        # Set up the test with mock data
        mock_query_results = [('database1',), ('database2',)]
        connection_uri = 'someuri'
        mock_cursor = MockCursor(mock_query_results)
        mock_cursor.fetchall.side_effect = psycopg2.ProgrammingError('')
        mock_connection = MockConnection(
            dsn_parameters={
                'host': 'myserver',
                'dbname': 'postgres',
                'user': 'postgres'
            },
            cursor=mock_cursor)
        psycopg2.connect = Mock(return_value=mock_connection)
        mock_request_context = utils.MockRequestContext()

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data({})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        self.connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Verify that calling the listdatabases handler returns the expected
        # databases
        params = ListDatabasesParams()
        params.owner_uri = connection_uri

        self.connection_service.handle_list_databases(mock_request_context, params)
        self.assertIsNone(mock_request_context.last_notification_method)
        self.assertIsNone(mock_request_context.last_notification_params)
        self.assertIsNone(mock_request_context.last_response_params)
        self.assertIsNotNone(mock_request_context.last_error_message)

    def test_build_connection_response(self):
        """Test that the connection response is built correctly"""
        # Set up the test with mock data
        server_name = 'testserver'
        db_name = 'testdb'
        user = 'testuser'
        mock_connection = MockConnection({
            'host': server_name,
            'dbname': db_name,
            'user': user
        })
        connection_type = ConnectionType.EDIT
        connection_details = ConnectionDetails.from_data(opts={})
        owner_uri = 'test_uri'
        connection_info = ConnectionInfo(owner_uri, connection_details)
        connection_info._connection_map = {connection_type: mock_connection}

        # If I build a connection response for the connection
        response = pgsqltoolsservice.connection.connection_service._build_connection_response(
            connection_info, connection_type)

        # Then the response should have accurate information about the connection
        self.assertEqual(response.owner_uri, owner_uri)
        self.assertEqual(response.server_info.server_version, mock_connection.server_version)
        self.assertEqual(response.server_info.is_cloud, False)
        self.assertEqual(response.connection_summary.server_name, server_name)
        self.assertEqual(response.connection_summary.database_name, db_name)
        self.assertEqual(response.connection_summary.user_name, user)
        self.assertEqual(response.type, connection_type)

    def test_default_database(self):
        """Test that if no database is given, the default database is used"""
        # Set up the connection params and default database name
        default_db = 'test_db'
        self.connection_service._service_provider[constants.WORKSPACE_SERVICE_NAME].configuration.pgsql.default_database = default_db
        psycopg2.connect = Mock()
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'user': 'postgres',
                    'password': 'password',
                    'host': 'myserver',
                    'dbname': ''
                }
            }
        })

        # If I connect with an empty database name
        with mock.patch('pgsqltoolsservice.connection.connection_service._build_connection_response'):
            self.connection_service.connect(params)

        # Then psycopg2's connect method was called with the default database
        calls = psycopg2.connect.mock_calls
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][2]['dbname'], default_db)

    def test_non_default_database(self):
        """Test that if a database is given, the default database is not used"""
        # Set up the connection params and default database name
        default_db = 'test_db'
        actual_db = 'postgres'
        self.connection_service._service_provider[constants.WORKSPACE_SERVICE_NAME].configuration.pgsql.default_database = default_db
        psycopg2.connect = Mock()
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'user': 'postgres',
                    'password': 'password',
                    'host': 'myserver',
                    'dbname': actual_db
                }
            }
        })

        # If I connect with an empty database name
        with mock.patch('pgsqltoolsservice.connection.connection_service._build_connection_response'):
            self.connection_service.connect(params)

        # Then psycopg2's connect method was called with the default database
        calls = psycopg2.connect.mock_calls
        self.assertEqual(len(calls), 1)
        self.assertNotEqual(calls[0][2]['dbname'], default_db)
        self.assertEqual(calls[0][2]['dbname'], actual_db)

    def test_get_connection_info(self):
        """Test that get_connection_info returns the ConnectionInfo object corresponding to a connection"""
        # Set up the test with mock data
        connection_uri = 'someuri'

        # Insert a ConnectionInfo object into the connection service's map
        connection_details = ConnectionDetails.from_data({})
        connection_info = ConnectionInfo(connection_uri, connection_details)
        self.connection_service.owner_to_connection_map[connection_uri] = connection_info

        # Get the connection info
        actual_connection_info = self.connection_service.get_connection_info(connection_uri)
        self.assertIs(actual_connection_info, connection_info)

    def test_get_connection_info_no_connection(self):
        """Test that get_connection_info returns None when there is no connection for the given owner URI"""
        # Set up the test with mock data
        connection_uri = 'someuri'

        # Get the connection info
        actual_connection_info = self.connection_service.get_connection_info(connection_uri)
        self.assertIsNone(actual_connection_info)


class TestConnectionCancellation(unittest.TestCase):
    """Methods for testing connection cancellation requests"""

    def setUp(self):
        """Set up the tests with common connection parameters"""
        # Set up the mock connection service and connection info
        self.connection_service = ConnectionService()
        self.connection_service._service_provider = {constants.WORKSPACE_SERVICE_NAME: WorkspaceService()}
        self.owner_uri = 'test_uri'
        self.connection_type = ConnectionType.DEFAULT
        self.connect_params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': self.owner_uri,
            'type': self.connection_type,
            'connection': {
                'options': {
                }
            }
        })
        self.mock_connection = MockConnection(dsn_parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'
        })

        # Mock psycopg2's connect method to store the current cancellation token. This lets us
        # capture the cancellation token state as it would be during a long-running connection.
        self.token_store = []

        def mock_connect(**kwargs):
            """Mock connection method to store the current cancellation token"""
            return self._mock_connect()

        psycopg2.connect = Mock(side_effect=mock_connect)

    def test_connecting_sets_cancellation_token(self):
        """Test that a cancellation token is set before a connection thread attempts to connect"""
        # If I attempt to connect
        response = self.connection_service.connect(self.connect_params)

        # Then the cancellation token should have been set and should not have been canceled
        self.assertEqual(len(self.token_store), 1)
        self.assertFalse(self.token_store[0].canceled)

        # And the cancellation token should have been cleared when the connection succeeded
        self.assertIsNone(response.error_message)
        self.assertFalse((self.owner_uri, self.connection_type) in self.connection_service._cancellation_map)

    def test_connection_failed_removes_own_token(self):
        """Test that the cancellation token is removed after a connection fails"""
        # Set up psycopg2's connection method to throw an error
        psycopg2.connect = Mock(side_effect=Exception())

        # If I attempt to connect
        response = self.connection_service.connect(self.connect_params)

        # Then the cancellation token should have been cleared when the connection failed
        self.assertIsNotNone(response.error_message)
        self.assertFalse((self.owner_uri, self.connection_type) in self.connection_service._cancellation_map)

    def test_connecting_cancels_previous_connection(self):
        """Test that opening a new connection while one is ongoing cancels the previous connection"""
        # Set up psycopg2's connection method to kick off a new connection. This simulates the case
        # where a call to psycopg2.connect is taking a long time and another connection request for
        # the same URI and connection type comes in and finishes before the current connection
        old_mock_connect = psycopg2.connect.side_effect

        def first_mock_connect(**kwargs):
            """Mock connection method to store the current cancellation token, and kick off another connection"""
            mock_connection = self._mock_connect()
            psycopg2.connect.side_effect = old_mock_connect
            self.connection_service.connect(self.connect_params)
            return mock_connection

        psycopg2.connect.side_effect = first_mock_connect

        # If I attempt to connect, and then kick off a new connection while connecting
        response = self.connection_service.connect(self.connect_params)

        # Then the connection should have been canceled and returned none
        self.assertIsNone(response)

        # And the recorded cancellation tokens should show that the first request was canceled
        self.assertEqual(len(self.token_store), 2)
        self.assertTrue(self.token_store[0].canceled)
        self.assertFalse(self.token_store[1].canceled)

    def test_newer_cancellation_token_not_removed(self):
        """Test that a newer connection's cancellation token is not removed after a connection completes"""
        # Set up psycopg2's connection method to simulate a new connection by overriding the
        # current cancellation token. This simulates the case where a call to psycopg2.connect is
        # taking a long time and another connection request for the same URI and connection type
        # comes in and finishes after the current connection
        cancellation_token = CancellationToken()
        cancellation_key = (self.owner_uri, self.connection_type)

        def override_mock_connect(**kwargs):
            """Mock connection method to override the current connection token, as if another connection is executing"""
            mock_connection = self._mock_connect()
            self.connection_service._cancellation_map[cancellation_key].cancel()
            self.connection_service._cancellation_map[cancellation_key] = cancellation_token
            return mock_connection

        psycopg2.connect.side_effect = override_mock_connect

        # If I attempt to connect, and the cancellation token gets updated while connecting
        response = self.connection_service.connect(self.connect_params)

        # Then the connection should have been canceled and returned none
        self.assertIsNone(response)

        # And the current cancellation token should not have been removed
        self.assertIs(self.connection_service._cancellation_map[cancellation_key], cancellation_token)

    def test_handle_cancellation_request(self):
        """Test that handling a cancellation request modifies the cancellation token for a matched connection"""
        # Set up the connection service with a mock request handler and cancellation token
        cancellation_key = (self.owner_uri, self.connection_type)
        cancellation_token = CancellationToken()
        self.connection_service._cancellation_map[cancellation_key] = cancellation_token
        request_context = utils.MockRequestContext()

        # If I call the cancellation request handler
        cancel_params = CancelConnectParams(self.owner_uri, self.connection_type)
        self.connection_service.handle_cancellation_request(request_context, cancel_params)

        # Then the handler should have responded and set the cancellation flag
        request_context.send_response.assert_called_once_with(True)
        self.assertTrue(cancellation_token.canceled)

    def test_handle_cancellation_no_match(self):
        """Test that handling a cancellation request returns false if there is no matching connection to cancel"""
        # Set up a mock request handler
        request_context = utils.MockRequestContext()

        # If I call the cancellation request handler
        cancel_params = CancelConnectParams(self.owner_uri, self.connection_type)
        self.connection_service.handle_cancellation_request(request_context, cancel_params)

        # Then the handler should have responded false to indicate that no matching connection was in progress
        request_context.send_response.assert_called_once_with(False)

    def _mock_connect(self):
        """Implementation for the mock psycopg2.connect method that saves the current cancellation token"""
        self.token_store.append(self.connection_service._cancellation_map[(self.owner_uri, self.connection_type)])
        return self.mock_connection


if __name__ == '__main__':
    unittest.main()
