# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the query execution service"""

from datetime import datetime
import unittest
from unittest import mock
from typing import List, Dict  # noqa

import psycopg2

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData)
import pgsqltoolsservice.utils
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.query_execution.contracts import (
    DbColumn, MESSAGE_NOTIFICATION, ResultSetSubset, SubsetParams, BATCH_COMPLETE_NOTIFICATION,
    BATCH_START_NOTIFICATION, QUERY_COMPLETE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION)
from pgsqltoolsservice.query_execution.batch import Batch, BatchSummary
from pgsqltoolsservice.query_execution.result_set import ResultSet
import tests.utils as utils


class TestQueryService(unittest.TestCase):
    """Methods for testing the query execution service"""

    def setUp(self):
        """Set up mock objects for testing the query execution service.
        Ran before each unit test.
        """
        self.cursor = utils.MockCursor(None)
        self.connection = utils.MockConnection(cursor=self.cursor)
        self.cursor.connection = self.connection
        self.connection_service = ConnectionService()
        self.connection_service.get_connection = mock.Mock(return_value=self.connection)
        self.query_execution_service = QueryExecutionService()
        self.service_provider = ServiceProvider(None, {})
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service}
        self.service_provider._is_initialized = True
        self.query_execution_service._service_provider = self.service_provider
        self.request_context = utils.MockRequestContext()

    def test_initialization(self):
        # Setup: Create a capabilities service with a mocked out service
        # provider
        mock_server_set_request = mock.MagicMock()
        mock_server = JSONRPCServer(None, None)
        mock_server.set_request_handler = mock_server_set_request
        mock_service_provider = ServiceProvider(mock_server, {}, None)
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

    def test_get_query_full(self):
        """Test getting a query for a URI from the entire file"""
        # Set up the service and the query
        query_execution_service = QueryExecutionService()
        params = ExecuteStringParams()
        params.query = 'select version()'
        # If I try to get a query using ExecuteStringParams
        result = query_execution_service._get_query_from_execute_params(params)
        # Then the retrieved query should be the same as the one on the params object
        self.assertEqual(result, params.query)

    def test_get_query_selection(self):
        """Test getting a query for a URI from a selection"""
        # Set up the query execution service with a mock workspace service
        query_execution_service = QueryExecutionService()
        query = 'select version()'
        mock_workspace_service = mock.Mock()
        mock_workspace_service.get_text = mock.Mock(return_value=query)
        query_execution_service._service_provider = {constants.WORKSPACE_SERVICE_NAME: mock_workspace_service}

        # Execute the query and verify that the workspace service's get_text
        # method was called
        # Set up the query params as an ExecuteDocumentSelectionParams object
        selection_data = SelectionData()
        selection_data.start_line = 0
        selection_data.start_column = 0
        selection_data.end_line = 0
        selection_data.end_column = 14
        params = ExecuteDocumentSelectionParams()
        params.owner_uri = 'test_uri'
        params.selection_data = selection_data

        # If I try to get a query using ExecuteDocumentSelectionParams
        result = query_execution_service._get_query_from_execute_params(params)

        # Then the query execution service calls the workspace service to get the query text
        mock_workspace_service.get_text.assert_called_once_with(params.owner_uri, mock.ANY)
        self.assertEqual(result, query)

    def test_get_query_selection_none(self):
        """Test getting a query for a URI from a selection when the selection is None (for the whole file)"""
        # Set up the query execution service with a mock workspace service
        query_execution_service = QueryExecutionService()
        query = 'select version()'
        mock_workspace_service = mock.Mock()
        mock_workspace_service.get_text = mock.Mock(return_value=query)
        query_execution_service._service_provider = {
            constants.WORKSPACE_SERVICE_NAME: mock_workspace_service}

        # Execute the query and verify that the workspace service's get_text
        # method was called
        # Set up the query params as an ExecuteDocumentSelectionParams object
        params = ExecuteDocumentSelectionParams()
        params.owner_uri = 'test_uri'
        params.selection_data = None

        # If I try to get a query using ExecuteDocumentSelectionParams
        result = query_execution_service._get_query_from_execute_params(params)

        # Then the query execution service calls the workspace service to get
        # the query text
        mock_workspace_service.get_text.assert_called_once_with(params.owner_uri, None)
        self.assertEqual(result, query)

    def test_query_request_invalid_uri(self):
        """Test handling a query request when the request has an invalid owner URI"""
        # Set up the query execution service and a connection service that has no known URIs
        query_execution_service = QueryExecutionService()
        service_provider = ServiceProvider(None, {})
        service_provider._logger = utils.get_mock_logger()
        service_provider._services = {constants.CONNECTION_SERVICE_NAME: ConnectionService()}
        service_provider._is_initialized = True
        query_execution_service._service_provider = service_provider

        # Set up the request context and request parameters
        mock_request_context = utils.MockRequestContext()
        params = get_execute_string_params()

        # If I try to handle a query request with an invalid owner URI
        query_execution_service._handle_execute_query_request(mock_request_context, params)

        # Then it responds with an error instead of a regular response
        mock_request_context.send_error.assert_called_once()
        mock_request_context.send_response.assert_not_called()

    def test_query_request_error_handling(self):
        """Test handling a query request that fails when the query is executed"""
        # Set up the query execution service and a connection service with a mock connection that
        # has a cursor that always throws an error when executing
        mock_cursor = utils.MockCursor(None)
        mock_cursor.execute = mock.Mock(side_effect=psycopg2.DatabaseError())
        mock_connection = utils.MockConnection(cursor=mock_cursor)
        connection_service = ConnectionService()
        connection_service.get_connection = mock.Mock(return_value=mock_connection)
        query_execution_service = QueryExecutionService()
        mock_service_provider = ServiceProvider(None, {})
        mock_service_provider._services = {constants.CONNECTION_SERVICE_NAME: connection_service}
        mock_service_provider._is_initialized = True
        query_execution_service._service_provider = mock_service_provider

        # Set up the request context and request parameters
        mock_request_context = utils.MockRequestContext()
        params = get_execute_string_params()

        # If I handle a query that raises an error when executed
        query_execution_service._handle_execute_query_request(mock_request_context, params)

        # Then the transaction gets rolled back, the cursor gets closed, and an error notification gets sent
        mock_connection.rollback.assert_called_once()
        mock_connection.commit.assert_not_called()
        mock_cursor.close.assert_called_once()
        mock_request_context.send_notification.assert_called()

        notification_calls = mock_request_context.send_notification.mock_calls
        # Get the message params for all message notifications that were sent
        call_params_list = [call[1][1] for call in notification_calls if call[1][0] == MESSAGE_NOTIFICATION]
        # Assert that at least one message notification was sent and that it was an error message
        self.assertGreater(len(call_params_list), 0)
        for call_params in call_params_list:
            self.assertTrue(call_params.message.is_error)

    def test_query_request_response(self):
        """Test that a response is sent when handling a query request"""
        # Set up the query execution service with a mock connection service
        connection_service = ConnectionService()
        connection_service.get_connection = mock.Mock(return_value=None)
        query_execution_service = QueryExecutionService()
        mock_service_provider = ServiceProvider(None, {})
        mock_service_provider._services = {constants.CONNECTION_SERVICE_NAME: connection_service}
        mock_service_provider._is_initialized = True
        query_execution_service._service_provider = mock_service_provider

        # Set up the request context and request parameters
        mock_request_context = utils.MockRequestContext()
        params = get_execute_string_params()

        # If I handle a query
        try:
            query_execution_service._handle_execute_query_request(mock_request_context, params)
        except BaseException:            # This test doesn't mock enough to actually execute the query
            pass

        # Then there should have been a response sent to my request
        mock_request_context.send_error.assert_not_called()
        mock_request_context.send_response.assert_called_once()

    def test_result_set_subset(self):
        """
        Test for proper generation of ResultSetSubset
        that is part of query/subset response payload
        """
        query_results: Dict[str, List[Batch]] = {}
        owner_uri = "untitled"
        query_results[owner_uri] = []
        batch_ordinal = 0
        result_ordinal = 0
        rows = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        query_results[owner_uri].append(Batch(batch_ordinal, SelectionData(), False))
        query_results[owner_uri][batch_ordinal].result_sets.append(
            ResultSet(result_ordinal, batch_ordinal, None, len(rows), rows))

        result_rows = query_results[owner_uri][batch_ordinal].result_sets[result_ordinal].rows
        results_size = len(result_rows)
        result_set_subset = ResultSetSubset(query_results, owner_uri, batch_ordinal,
                                            result_ordinal, 0, results_size)

        row_size = 3
        self.assertEquals(results_size, result_set_subset.row_count)
        db_cell_values = result_set_subset.rows
        values_len = len(db_cell_values)
        self.assertEqual(values_len, results_size)

        # Check that the DbColumn[][] is generated correctly
        for row_index in range(0, values_len):
            row_len = len(db_cell_values[row_index])
            self.assertEqual(row_len, row_size)
            row = db_cell_values[row_index]
            for column_index in range(0, row_len):
                result_cell = result_rows[row_index][column_index]
                cell = row[column_index]
                self.assertEqual(cell.display_value, None if result_cell is None else str(result_cell))
                self.assertEqual(cell.is_null, result_cell is None)
                self.assertEqual(cell.row_id, row_index)

        # Test that we raise Value Errors when using incorrect indices
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, -1, result_ordinal, 0, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, 1, result_ordinal, 0, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, 500, 0, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, -1, 0, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, result_ordinal, 0, results_size + 1)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, result_ordinal, 2, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, result_ordinal, -1, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, owner_uri, batch_ordinal, result_ordinal, 0, -1)

    def test_result_set_positive(self):
        """Test that we properly generate the result set"""
        description = [("first", 0, 1, 2, 3, 4, True), ("second", 5, 6, 7, 8, 9, False)]
        test_columns = [DbColumn(0, description[0]), DbColumn(1, description[1])]
        ordinal = 0
        batch_ordinal = 0
        row_count = len(description)

        result_set = ResultSet(ordinal, batch_ordinal, description, row_count, [])
        self.assertEqual(len(test_columns), len(result_set.columns))

        for index in range(0, len(test_columns)):
            self.assertEqual(test_columns[index].__dict__, result_set.columns[index].__dict__)
        self.assertEqual(ordinal, result_set.id)
        self.assertEqual(batch_ordinal, result_set.batch_id)
        self.assertEqual(0, result_set.total_bytes_written)
        self.assertEqual(None, result_set.output_file_name)
        self.assertEqual([], result_set.file_offsets)
        self.assertEqual(0, result_set.special_action.flags)
        self.assertEqual(False, result_set.has_been_read)
        self.assertEqual([], result_set.save_tasks)
        self.assertEqual(None, result_set.is_single_column_xml_json_result_set)
        self.assertEqual(None, result_set.output_file_name)
        self.assertEqual(None, result_set.row_count_override)
        self.assertEqual(row_count, result_set.row_count)
        self.assertEqual([], result_set.rows)

    def test_result_set_column_none_description(self):
        """Test that result set column is empty if description is None.
        Description is None if there were no results for a query
        """
        description = None
        result_set = ResultSet(0, 0, description, 0, [])
        self.assertEqual([], result_set.columns)

    def test_result_set_complete_params(self):
        """Test building parameters for the result set complete notification"""
        # Set up the test with a batch summary and owner uri
        batch = Batch(10, SelectionData(), False)
        batch.has_executed = True
        batch.result_sets = [ResultSet(1, 10, None, 0, [])]
        summary = batch.build_batch_summary()
        owner_uri = 'test_uri'

        # Set up the mock query execution service
        query_execution_service = QueryExecutionService()
        query_execution_service._service_provider = ServiceProvider(None, {}, utils.get_mock_logger())

        # If I build a result set complete response from the summary
        result = query_execution_service.build_result_set_complete_params(summary, owner_uri)

        # Then the parameters should have an owner uri and result set summary that matches the ones provided
        self.assertEqual(result.owner_uri, owner_uri)
        self.assertEqual(result.result_set_summary, summary.result_set_summaries[0])

    def test_message_notices_no_error(self):
        """Test to make sure that notices are being sent as part of a message notification"""
        # Set up params that are sent as part of a query execution request
        params = get_execute_string_params()
        # If we handle an execute query request
        self.query_execution_service._handle_execute_query_request(self.request_context, params)

        # Then we executed the query, closed the cursor, and called fetchall once each.
        # And the connection's notices is set properly
        self.cursor.execute.assert_called_once()
        self.cursor.close.assert_called_once()
        self.cursor.fetchall.assert_called_once()
        self.assertEqual(self.connection.notices, [])

        # Get the message params for all message notifications that were sent
        # call[0] would refer to the name of the notification call. call[1] allows
        # access to the arguments list of the notification call
        notification_calls = self.request_context.send_notification.mock_calls
        call_params_list = [call[1][1] for call in notification_calls if call[1][0] == MESSAGE_NOTIFICATION]

        # Assert that at least one message notification was sent and that there were no errors
        self.assertGreaterEqual(len(call_params_list), 1)
        for param in call_params_list:
            self.assertFalse(param.message.is_error)

        # The first message should have the notices
        expected_notices = ["NOTICE: foo", "DEBUG: bar"]
        subset = ''.join(expected_notices)
        self.assertTrue(subset in call_params_list[0].message.message)

    def test_message_notices_error(self):
        """Test that the notices are being sent as part of messages correctly in the case of
        an error during execution of a query
        """
        # Set up query execution side effect and params sent as part of a QE request
        self.cursor.execute = mock.Mock(side_effect=self.cursor.execute_failure_side_effects)
        params = get_execute_string_params()

        # If we handle an execute query request
        self.query_execution_service._handle_execute_query_request(self.request_context, params)

        # Then we executed the query, closed the cursor,
        # did not call fetchall(), and cleared the notices
        self.cursor.execute.assert_called_once()
        self.cursor.close.assert_called_once()
        self.cursor.fetchall.assert_not_called()
        self.assertEqual(self.connection.notices, [])

        # Get the message params for all message notifications that were sent
        # call[0] would refer to the name of the notification call. call[1] allows
        # access to the arguments list of the notification call
        notification_calls = self.request_context.send_notification.mock_calls
        call_params_list = [call[1][1] for call in notification_calls if call[1][0] == MESSAGE_NOTIFICATION]

        # Assert that only two message notifications were sent.
        # The first is a message containing only the notifications, where is_error is false
        # The second is the error message, where is_error is true
        expected_notices = ["NOTICE: foo", "DEBUG: bar"]
        self.assertEqual(len(call_params_list), 2)
        self.assertFalse(call_params_list[0].message.is_error)
        self.assertTrue(call_params_list[1].message.is_error)
        notices_str = ''.join(expected_notices)

        # Make sure that the whole first message consists of the notices, as expected
        self.assertEqual(notices_str, call_params_list[0].message.message)

    def test_query_execution(self):
        """Test that query execution sends the proper response/notices to the client"""
        # Set up params that are sent as part of a query execution request
        params = get_execute_string_params()

        # If we handle an execute query request
        self.query_execution_service._handle_execute_query_request(self.request_context, params)

        # Then we executed the query, closed the cursor, and called fetchall once each.
        self.cursor.execute.assert_called_once()
        self.cursor.close.assert_called_once()
        self.cursor.fetchall.assert_called_once()

        # And we sent a response to the initial query
        self.request_context.send_response.assert_called_once_with({})
        notification_calls = self.request_context.send_notification.mock_calls
        call_args_list = [call[1] for call in notification_calls]

        # And a batch start notification
        batch_start_params_list = [args[1] for args in call_args_list if args[0] == BATCH_START_NOTIFICATION]
        result_set_params_list = [args[1] for args in call_args_list if args[0] == RESULT_SET_COMPLETE_NOTIFICATION]
        message_params_list = [args[1] for args in call_args_list if args[0] == MESSAGE_NOTIFICATION]
        batch_complete_params_list = [args[1] for args in call_args_list if args[0] == BATCH_COMPLETE_NOTIFICATION]
        query_complete_params_list = [args[1] for args in call_args_list if args[0] == QUERY_COMPLETE_NOTIFICATION]
        self.assertEqual(len(batch_start_params_list), 1)
        self.assertEqual(len(result_set_params_list), 1)
        self.assertGreaterEqual(len(message_params_list), 1)
        self.assertEqual(len(batch_complete_params_list), 1)
        self.assertEqual(len(query_complete_params_list), 1)

    def test_handle_subset_request(self):
        """Test that the query execution service handles subset requests correctly"""
        # Set up the test with the proper parameters and query results
        params = SubsetParams.from_dict({
            'owner_uri': 'test_uri',
            'batch_index': 2,
            'result_set_index': 0,
            'rows_start_index': 1,
            'rows_count': 2
        })
        batch = Batch(2, SelectionData(), False)
        batch_rows = [(1, 2), (3, 4), (5, 6)]
        batch.result_sets = [ResultSet(0, 0, {}, 3, batch_rows)]
        self.query_execution_service.query_results = {
            params.owner_uri: [Batch(0, SelectionData(), False), Batch(1, SelectionData(), False), batch],
            'some_other_uri': [Batch(3, SelectionData(), False)]
        }

        # If I call the subset request handler
        self.query_execution_service._handle_subset_request(self.request_context, params)

        # Then the response should match the subset we requested
        response = self.request_context.last_response_params
        result_subset = response.result_subset
        self.assertEqual(len(result_subset.rows), params.rows_count)
        self.assertEqual(result_subset.row_count, params.rows_count)
        self.assertEqual(len(result_subset.rows[0]), 2)
        self.assertEqual(len(result_subset.rows[1]), 2)
        self.assertEqual(result_subset.rows[0][0].display_value, str(batch_rows[1][0]))
        self.assertEqual(result_subset.rows[0][1].display_value, str(batch_rows[1][1]))
        self.assertEqual(result_subset.rows[1][0].display_value, str(batch_rows[2][0]))
        self.assertEqual(result_subset.rows[1][1].display_value, str(batch_rows[2][1]))


def get_execute_string_params() -> ExecuteStringParams:
    """Get a simple ExecutestringParams"""
    params = ExecuteStringParams()
    params.query = 'select version()'
    params.owner_uri = 'test_uri'
    return params


if __name__ == '__main__':
    unittest.main()
