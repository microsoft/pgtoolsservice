import unittest
from unittest import mock

import pymysql

import tests.utils as utils
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.hosting import (IncomingMessageConfiguration,
                                       JSONRPCServer, ServiceProvider)
from ossdbtoolsservice.query_execution.contracts import (
    BATCH_COMPLETE_NOTIFICATION, BATCH_START_NOTIFICATION,
    MESSAGE_NOTIFICATION, QUERY_COMPLETE_NOTIFICATION,
    RESULT_SET_COMPLETE_NOTIFICATION)
from ossdbtoolsservice.query_execution.query_execution_service import \
    QueryExecutionService
from ossdbtoolsservice.utils import constants
from tests.mysqlsmo_tests.utils import MockMySQLServerConnection

from .test_pg_query_execution_service import get_execute_string_params


class TestQueryService(unittest.TestCase):
    """Methods for testing the query execution service"""

    def setUp(self):
        """Set up mock objects for testing the query execution service.
        Ran before each unit test.
        """
        # set up mock connection
        self.rows = [(1, 'Text 1'), (2, 'Text 2')]
        self.cursor = utils.MockCursor(self.rows)
        self.mock_pymysql_connection = utils.MockPyMySQLConnection(parameters={
            'host': 'test',
            'dbname': 'test',
        })
        self.connection = MockMySQLServerConnection(self.cursor)
        self.cursor.connection = self.connection
        self.connection_service = ConnectionService()
        self.request_context = utils.MockRequestContext()

        # setup mock query_execution_service
        self.query_execution_service = QueryExecutionService()
        self.service_provider = ServiceProvider(None, {}, constants.MYSQL_PROVIDER_NAME)
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service}
        self.service_provider._is_initialized = True
        self.query_execution_service._service_provider = self.service_provider

        def connection_side_effect(owner_uri: str, connection_type: ConnectionType):
            return self.connection

        self.connection_service.get_connection = mock.Mock(side_effect=connection_side_effect)

    def test_initialization(self):
        # Setup: Create a capabilities service with a mocked out service
        # provider
        mock_server_set_request = mock.MagicMock()
        mock_server = JSONRPCServer(None, None)
        mock_server.set_request_handler = mock_server_set_request
        mock_service_provider = ServiceProvider(mock_server, {}, constants.MYSQL_PROVIDER_NAME, None)
        service = QueryExecutionService()

        # If: I initialize the service
        service.register(mock_service_provider)

        # Then:
        # ... There should have been request handlers set
        mock_server_set_request.assert_called()

        # ... Each mock call should have an IncomingMessageConfig and a function pointer
        for mock_call in mock_server_set_request.mock_calls:
            self.assertIsInstance(
                mock_call[1][0], IncomingMessageConfiguration)
            self.assertTrue(callable(mock_call[1][1]))

    def test_query_request_error_handling(self):
        """Test handling a query request that fails when the query is executed"""
        # Set up the query execution service and a connection service with a mock connection that
        # has a cursor that always throws an error when executing
        self.cursor.execute = mock.Mock(side_effect=pymysql.err.DatabaseError())
        params = get_execute_string_params()

        # If I handle a query that raises an error when executed
        self.query_execution_service._handle_execute_query_request(self.request_context, params)
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

        # Then the transaction gets rolled back, the cursor does not get manually closed, and an error notification gets sent
        self.cursor.close.assert_not_called()
        self.request_context.send_notification.assert_called()

        notification_calls = self.request_context.send_notification.mock_calls
        # Get the message params for all message notifications that were sent
        call_params_list = [call[1][1] for call in notification_calls if call[1][0] == MESSAGE_NOTIFICATION]
        # Assert that at least one message notification was sent and that it was an error message
        self.assertGreater(len(call_params_list), 0)
        for call_params in call_params_list:
            self.assertTrue(call_params.message.is_error)

    def test_query_execution(self):
        """Test that query execution sends the proper response/notices to the client"""
        # Set up params that are sent as part of a query execution request
        params = get_execute_string_params()

        columns_info = []
        with mock.patch('ossdbtoolsservice.query.data_storage.storage_data_reader.get_columns_info', new=mock.Mock(return_value=columns_info)):
            # If we handle an execute query request
            self.query_execution_service._handle_execute_query_request(self.request_context, params)
            self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

        # Then we executed the query, closed the cursor, and called fetchall once each.
        self.cursor.execute.assert_called_once()
        self.cursor.close.assert_called_once()

        # And we sent a response to the initial query, along with notifications for
        # query/batchStart, query/resultSetComplete, query/message, query/batchComplete,
        # and query/complete
        self.request_context.send_response.assert_called_once_with({})
        notification_calls = self.request_context.send_notification.mock_calls
        call_methods_list = [call[1][0] for call in notification_calls]
        self.assertEqual(call_methods_list.count(BATCH_START_NOTIFICATION), 1)
        self.assertEqual(call_methods_list.count(RESULT_SET_COMPLETE_NOTIFICATION), 1)
        self.assertGreaterEqual(call_methods_list.count(MESSAGE_NOTIFICATION), 1)
        self.assertEqual(call_methods_list.count(BATCH_COMPLETE_NOTIFICATION), 1)
        self.assertEqual(call_methods_list.count(QUERY_COMPLETE_NOTIFICATION), 1)
