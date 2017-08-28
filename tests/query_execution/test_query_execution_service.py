# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the query execution service"""

import unittest
from unittest import mock
from typing import List, Dict  # noqa

import psycopg2
from dateutil import parser
import uuid

from pgsqltoolsservice.connection import ConnectionService, ConnectionInfo
from pgsqltoolsservice.query_execution.query_execution_service import (
    QueryExecutionService, CANCELATION_QUERY, NO_QUERY_MESSAGE, ExecuteRequestWorkerArgs)
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData, ExecuteRequestParamsBase)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.query_execution.contracts import (
    DbColumn, MESSAGE_NOTIFICATION, ResultSetSubset, SubsetParams, BATCH_COMPLETE_NOTIFICATION,
    BATCH_START_NOTIFICATION, QUERY_COMPLETE_NOTIFICATION, RESULT_SET_COMPLETE_NOTIFICATION,
    QueryCancelResult, QueryDisposeParams, SimpleExecuteRequest)
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.query import Query, ExecutionState
from pgsqltoolsservice.query_execution.result_set import ResultSet
import tests.utils as utils
from pgsqltoolsservice.connection.contracts import ConnectionType, ConnectionDetails
from pgsqltoolsservice.query_execution.contracts.common import SubsetResult


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
        self.query_execution_service = QueryExecutionService()
        self.service_provider = ServiceProvider(None, {})
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service}
        self.service_provider._is_initialized = True
        self.query_execution_service._service_provider = self.service_provider
        self.request_context = utils.MockRequestContext()

        self.cursor_cancel = utils.MockCursor(None)
        self.connection_cancel = utils.MockConnection(cursor=self.cursor_cancel)
        self.cursor_cancel.connection = self.connection_cancel

        def connection_side_effect(owner_uri: str, connection_type: ConnectionType):
            if connection_type is ConnectionType.QUERY_CANCEL:
                return self.connection_cancel
            else:
                return self.connection

        self.connection_service.get_connection = mock.Mock(side_effect=connection_side_effect)

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
        result = query_execution_service._get_query_text_from_execute_params(params)
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
        result = query_execution_service._get_query_text_from_execute_params(params)

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
        result = query_execution_service._get_query_text_from_execute_params(params)

        # Then the query execution service calls the workspace service to get
        # the query text
        mock_workspace_service.get_text.assert_called_once_with(params.owner_uri, None)
        self.assertEqual(result, query)

    def test_query_request_invalid_uri(self):
        """Test handling a query request when the request has an invalid owner URI"""
        # Set up the query execution service and a connection service that has no known URIs
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: ConnectionService()}
        params = get_execute_string_params()

        # If I try to handle a query request with an invalid owner URI
        self.query_execution_service._handle_execute_query_request(self.request_context, params)

        # Then it responds with an error instead of a regular response
        self.request_context.send_unhandled_error_response.assert_called_once()
        self.request_context.send_response.assert_not_called()

    def test_query_request_error_handling(self):
        """Test handling a query request that fails when the query is executed"""
        # Set up the query execution service and a connection service with a mock connection that
        # has a cursor that always throws an error when executing
        self.cursor.execute = mock.Mock(side_effect=psycopg2.DatabaseError())
        params = get_execute_string_params()

        # If I handle a query that raises an error when executed
        self.query_execution_service._handle_execute_query_request(self.request_context, params)
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

        # Then the transaction gets rolled back, the cursor gets closed, and an error notification gets sent
        self.cursor.close.assert_called_once()
        self.request_context.send_notification.assert_called()

        notification_calls = self.request_context.send_notification.mock_calls
        # Get the message params for all message notifications that were sent
        call_params_list = [call[1][1] for call in notification_calls if call[1][0] == MESSAGE_NOTIFICATION]
        # Assert that at least one message notification was sent and that it was an error message
        self.assertGreater(len(call_params_list), 0)
        for call_params in call_params_list:
            self.assertTrue(call_params.message.is_error)

    def test_query_request_response(self):
        """Test that a response is sent when handling a query request"""
        params = get_execute_string_params()

        # If I handle a query
        try:
            self.query_execution_service._handle_execute_query_request(self.request_context, params)
            self.query_execution_service.owner_to_thread_map[params.owner_uri].join()
        except BaseException:            # This test doesn't mock enough to actually execute the query
            pass

        # Then there should have been a response sent to my request
        self.request_context.send_error.assert_not_called()
        self.request_context.send_response.assert_called_once()

    def test_result_set_subset(self):
        """
        Test for proper generation of ResultSetSubset
        that is part of query/subset response payload
        """
        query_results: Dict[str, Query] = {}
        owner_uri = "untitled"
        query_results[owner_uri] = Query(owner_uri, '')
        batch_ordinal = 0
        result_ordinal = 0
        rows = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        query_results[owner_uri].batches.append(Batch('', batch_ordinal, SelectionData()))
        query_results[owner_uri].batches[batch_ordinal].result_set = ResultSet(result_ordinal, batch_ordinal, None, len(rows), rows)

        result_rows = query_results[owner_uri].batches[batch_ordinal].result_set.rows
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
        test_columns = [DbColumn.from_cursor_description(0, description[0]), DbColumn.from_cursor_description(1, description[1])]
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
        batch = Batch('', 10, SelectionData())
        batch.has_executed = True
        batch.result_set = ResultSet(1, 10, None, 0, [])
        summary = batch.build_batch_summary()
        owner_uri = 'test_uri'

        # If I build a result set complete response from the summary
        result = self.query_execution_service.build_result_set_complete_params(summary, owner_uri)

        # Then the parameters should have an owner uri and result set summary that matches the ones provided
        self.assertEqual(result.owner_uri, owner_uri)
        self.assertEqual(result.result_set_summary, summary.result_set_summaries[0])

    def test_message_notices_no_error(self):
        """Test to make sure that notices are being sent as part of a message notification"""
        # Set up params that are sent as part of a query execution request
        params = get_execute_string_params()
        # If we handle an execute query request
        self.query_execution_service._handle_execute_query_request(self.request_context, params)
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()
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
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

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

    def test_cancel_query_during_query_execution(self):
        """
        Test that we handle query cancellation requests correctly
        if we receive a cancel request during cursor.execute() call
        """
        execute_params = get_execute_string_params()
        cancel_params = get_execute_request_params()

        def cancel_during_execute_side_effects(*args):
            self.query_execution_service._handle_cancel_query_request(self.request_context, cancel_params)

        # Set up to run cancel query handler during execute() attempt
        self.cursor.execute = mock.Mock(side_effect=cancel_during_execute_side_effects)

        # If we attempt to execute a batch where we get an execute request in the middle of attempted execution
        self.query_execution_service._handle_execute_query_request(self.request_context, execute_params)
        # Wait for query execution worker thread to finish
        self.query_execution_service.owner_to_thread_map[execute_params.owner_uri].join()
        query = self.query_execution_service.query_results['test_uri']

        # Then we must have ran execute for a batch, and executed 'SELECTED pg_cancel_backend(pid)
        # to cancel the query
        self.cursor.execute.assert_called_once()
        self.cursor_cancel.execute.assert_called_once()
        self.assertTrue(isinstance(self.request_context.last_response_params, QueryCancelResult))
        self.assertEqual(self.request_context.last_response_params.messages, None)

        # Check the positional args for the first arg of of the first (and only) call
        # is the query string to cancel the ongoing query
        self.assertEqual(self.cursor_cancel.execute.call_args_list[0][0][0], CANCELATION_QUERY)

        # The batch is also marked as canceled and executed. There should have been no commits and
        # we should have rolled back. During execute_query call,
        self.assertTrue(query.is_canceled)
        self.assertEqual(query.execution_state, ExecutionState.EXECUTED)

    def test_cancel_query_before_query_execution(self):
        """
        Test that we handle query cancellation requests correctly
        if we receive a cancel request before cursor.execute() call
        """
        # Set up params
        execute_params = get_execute_string_params()
        cancel_params = get_execute_request_params()

        # Create a side effect to cancel the query while responding to the query request
        real_send_response = self.request_context.send_response

        def cancel_before_execute_side_effect(*args):
            real_send_response(*args)
            self.request_context.send_response.side_effect = real_send_response
            self.query_execution_service._handle_cancel_query_request(self.request_context, cancel_params)

        # Set the send_response method to have a side effect of cancelling the query, so that when we send the empty
        # response for starting the query, the query gets canceled. The side effect also resets send_response to its
        # normal behavior, so that the response to the cancel query request does not try to cancel the query again.
        self.request_context.send_response = mock.Mock(side_effect=cancel_before_execute_side_effect)

        # If we start the execute query request handler with a cancel query request before the query execution
        self.query_execution_service._handle_execute_query_request(self.request_context, execute_params)
        self.query_execution_service.owner_to_thread_map[execute_params.owner_uri].join()
        query = self.query_execution_service.query_results[execute_params.owner_uri]

        # Then the execute request handler's execute is not called,
        # as well as the cancel query's execute of 'SELECT pg_cancel_backend(pid) is called,
        # but doesn't do anything
        self.cursor.execute.assert_not_called()
        self.cursor_cancel.execute.assert_called_once()
        self.assertTrue(isinstance(self.request_context.last_response_params, QueryCancelResult))
        self.assertEqual(self.request_context.last_response_params.messages, None)
        # Check the positional args for the first arg of of the first (and only) call
        # is the query string to cancel the ongoing query
        self.assertEqual(self.cursor_cancel.execute.call_args_list[0][0][0], CANCELATION_QUERY)

        # The batch should be marked as canceled, the state should be executed, and we should have rolled back
        self.assertTrue(query.is_canceled)
        self.assertEqual(query.execution_state, ExecutionState.EXECUTED)

    def test_cancel_query_after_query_execution(self):
        """
        Test that we handle query cancellation requests correctly
        if we receive a cancel request after cursor.execute() call
        """

        # Set up params
        execute_params = get_execute_string_params()
        cancel_params = get_execute_request_params()

        # If we start the execute query request handler with the cancel query
        # request handled after the execute_query() and cursor.execute() calls
        self.query_execution_service._handle_execute_query_request(self.request_context, execute_params)
        self.query_execution_service.owner_to_thread_map[execute_params.owner_uri].join()
        self.query_execution_service._handle_cancel_query_request(self.request_context, cancel_params)
        query = self.query_execution_service.query_results['test_uri']

        # Then execute() in the execute query handler should have been called and
        # the cancel cursor's execute() should not have been called
        self.cursor.execute.assert_called_once()
        self.cursor_cancel.execute.assert_not_called()
        self.assertTrue(isinstance(self.request_context.last_response_params, QueryCancelResult))
        self.assertIsNotNone(self.request_context.last_response_params.messages)

        # And the query should executed but not canceled.
        self.assertFalse(query.is_canceled)
        self.assertEqual(query.execution_state, ExecutionState.EXECUTED)

    def test_query_execution(self):
        """Test that query execution sends the proper response/notices to the client"""
        # Set up params that are sent as part of a query execution request
        params = get_execute_string_params()

        # If we handle an execute query request
        self.query_execution_service._handle_execute_query_request(self.request_context, params)
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

        # Then we executed the query, closed the cursor, and called fetchall once each.
        self.cursor.execute.assert_called_once()
        self.cursor.close.assert_called_once()
        self.cursor.fetchall.assert_called_once()

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
        batch.result_set = ResultSet(0, 0, {}, 3, batch_rows)
        test_query = Query(params.owner_uri, '')
        test_query.batches = [Batch('', 0, SelectionData()), Batch('', 1, SelectionData()), batch]
        other_query = Query('some_other_uri', '')
        other_query.batches = [Batch('', 3, SelectionData())]
        self.query_execution_service.query_results = {
            test_query.owner_uri: test_query,
            other_query.owner_uri: other_query
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

    def test_time(self):
        """Test to see that the start, end, and execution times are properly set"""

        # Set up and run handler for executing queries
        params = get_execute_string_params()
        self.query_execution_service._handle_execute_query_request(self.request_context, params)
        self.query_execution_service.owner_to_thread_map[params.owner_uri].join()

        # Grab all notification calls and make sure that we call the notifications that we're interested in
        # exactly once
        notification_calls = self.request_context.send_notification.mock_calls
        call_methods_list = [call[1][0] for call in notification_calls]
        self.assertEqual(call_methods_list.count(BATCH_START_NOTIFICATION), 1)
        self.assertEqual(call_methods_list.count(BATCH_COMPLETE_NOTIFICATION), 1)
        self.assertEqual(call_methods_list.count(QUERY_COMPLETE_NOTIFICATION), 1)

        start_time = None
        for call in notification_calls:
            # Check that only the execution start time is defined for batch start
            if call[1][0] is BATCH_START_NOTIFICATION:
                start_time = call[1][1].batch_summary.execution_start
                self.assertIsNotNone(start_time)
                self.assertIsNone(call[1][1].batch_summary.execution_end)
                self.assertIsNone(call[1][1].batch_summary.execution_elapsed)
            elif call[1][0] is BATCH_COMPLETE_NOTIFICATION or call[1][0] is QUERY_COMPLETE_NOTIFICATION:
                # Set batch summary depending on complete notification type
                batch_summary = None
                if call[1][0] is BATCH_COMPLETE_NOTIFICATION:
                    batch_summary = call[1][1].batch_summary
                else:
                    self.assertEqual(len(call[1][1].batch_summaries), 1)
                    batch_summary = call[1][1].batch_summaries[0]
                # Make sure that all time-related fields are set and make sense
                self.assertEqual(start_time, batch_summary.execution_start)
                self.assertIsNotNone(batch_summary.execution_start)
                self.assertIsNotNone(batch_summary.execution_end)
                self.assertIsNotNone(batch_summary.execution_elapsed)
                self.assertLessEqual(parser.parse(batch_summary.execution_start), parser.parse(batch_summary.execution_end))
                self.assertEqual(batch_summary.execution_elapsed, str(parser.parse(batch_summary.execution_end) - parser.parse(batch_summary.execution_start)))

    def test_query_disposal_success_executed(self):
        """
        Test for handling query/dispose request in case where disposal is possible
        and query that we're attempting to dispose is already finished executing
        """
        # Initialize results
        uri = 'test_uri'
        self.query_execution_service.query_results[uri] = Query(uri, '')
        self.query_execution_service.query_results[uri].execution_state = ExecutionState.EXECUTED
        params = QueryDisposeParams()
        params.owner_uri = uri

        # If we attempt to dispose of an existing owner uri's query results when the result is populated
        self.query_execution_service._handle_dispose_request(self.request_context, params)

        # Then the uri key should no longer be in the results, and we sent an empty response
        self.assertTrue(uri not in self.query_execution_service.query_results)
        self.request_context.send_response.assert_called_once_with({})
        self.request_context.send_error.assert_not_called()
        self.cursor_cancel.execute.assert_not_called()

    def test_query_disposal_failure(self):
        """Test for handling query/dispose request in case where disposal is not possible"""
        # Note that query_results[uri] is never populated
        uri = 'test_uri'
        params = QueryDisposeParams()
        params.owner_uri = uri

        # If we attempt to dispose of a query result that doesn't exist
        self.query_execution_service._handle_dispose_request(self.request_context, params)

        # Then that result still doesn't exist, and we send an error as a response
        self.assertTrue(uri not in self.query_execution_service.query_results)
        self.request_context.send_response.assert_not_called()
        self.request_context.send_error.assert_called_once_with(NO_QUERY_MESSAGE)

    def test_query_disposal_with_query_executing(self):
        """Test query disposal while a query is executing"""
        uri = 'test_uri'
        self.query_execution_service.query_results[uri] = Query(uri, '')
        self.query_execution_service.query_results[uri].execution_state = ExecutionState.EXECUTING
        params = QueryDisposeParams()
        params.owner_uri = uri

        self.query_execution_service._handle_dispose_request(self.request_context, params)

        self.assertTrue(uri not in self.query_execution_service.query_results)
        self.request_context.send_response.assert_called_once_with({})
        self.request_context.send_error.assert_not_called()
        self.cursor_cancel.execute.assert_called_once()
        # Check the positional args for the first arg of of the first (and only) call
        # is the query string to cancel the ongoing query
        self.assertEqual(self.cursor_cancel.execute.call_args_list[0][0][0], CANCELATION_QUERY)

    def test_query_disposal_with_query_not_started(self):
        """Test query disposal while a query has not started executing"""
        uri = 'test_uri'
        self.query_execution_service.query_results[uri] = Query(uri, '')
        params = QueryDisposeParams()
        params.owner_uri = uri

        self.query_execution_service._handle_dispose_request(self.request_context, params)

        self.assertTrue(uri not in self.query_execution_service.query_results)
        self.request_context.send_response.assert_called_once_with({})
        self.request_context.send_error.assert_not_called()
        self.cursor_cancel.execute.assert_called_once()
        # Check the positional args for the first arg of of the first (and only) call
        # is the query string to cancel the ongoing query
        self.assertEqual(self.cursor_cancel.execute.call_args_list[0][0][0], CANCELATION_QUERY)

    def test_execution_error_rolls_back_transaction(self):
        """Test that a query execution error in the middle of a transaction causes that transaction to roll back"""
        # Set up the cursor to throw an error when executing and the connection to indicate that a transaction is open
        self.cursor.execute.side_effect = self.cursor.execute_failure_side_effects
        self.connection.get_transaction_status.return_value = psycopg2.extensions.TRANSACTION_STATUS_INERROR
        query_params = get_execute_string_params()
        self.query_execution_service.query_results[query_params.owner_uri] = Query(query_params.owner_uri, query_params.query)

        # If I execute a query that opens a transaction and then throws an error when executed

        worker_args = ExecuteRequestWorkerArgs(query_params.owner_uri, self.connection, self.request_context)

        self.query_execution_service._execute_query_request_worker(worker_args)

        # Then a rollback transaction should have been executed
        self.cursor.execute.assert_has_calls([mock.call(query_params.query), mock.call('ROLLBACK')])

    def test_handle_simple_execute_request(self):
        """ Test for _handle_simple_execute_request to make sure it returns required details
        from the first batch """
        simple_execution_request = SimpleExecuteRequest()
        simple_execution_request.owner_uri = 'test_uri'
        simple_execution_request.query_string = 'Select something'
        connection_uri = 'test_connection_url'

        connection_details = ConnectionDetails.from_data('myserver', 'postgres', 'postgres', {})
        connection_info = ConnectionInfo(connection_uri, connection_details)

        def get_connection_info(uri):
            self.assertEqual(uri, simple_execution_request.owner_uri)
            return connection_info

        self.connection_service.get_connection_info = mock.Mock(side_effect=get_connection_info)
        self.connection_service.connect = mock.MagicMock()

        mock_rows = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        new_owner_uri = str(uuid.uuid4())
        query = Query(new_owner_uri, '')
        rows = mock_rows
        batch = Batch('', 0, SelectionData())
        result_set = ResultSet(0, 0, None, len(rows), rows)
        batch.result_set = result_set
        batch.has_executed = True
        query.batches = [batch]
        self.query_execution_service.query_results = {
            new_owner_uri: query
        }
        query.execute = mock.MagicMock()

        def get_result_subset_mock(request_context, subset_params):

            self.assertEqual(self.request_context, request_context)
            self.assertEqual(subset_params.owner_uri, new_owner_uri)
            self.assertEqual(subset_params.batch_index, 0)
            self.assertEqual(subset_params.result_set_index, 0)
            self.assertEqual(subset_params.rows_start_index, 0)
            self.assertEqual(subset_params.rows_count, 2)

            subset = SubsetMock()
            subset.row_count = len(mock_rows)
            subset.rows = mock_rows

            result = SubsetResult(subset)

            return result

        self.query_execution_service._get_result_subset = mock.Mock(side_effect=get_result_subset_mock)

        def send_response_mock(args):
            self.assertEqual(args.rows, mock_rows)
            self.assertEqual(args.row_count, len(mock_rows))

        self.request_context.send_response = mock.Mock(side_effect=send_response_mock)

        with mock.patch('uuid.uuid4', new=mock.Mock(return_value=new_owner_uri)):
            self.query_execution_service._handle_simple_execute_request(self.request_context, simple_execution_request)


class SubsetMock:

    def __init__(self):
        self.rows = None
        self.row_count = None


class TestQueryAndBatchObjects(unittest.TestCase):
    """Unit tests for Query and Batch objects"""

    def setUp(self):
        """Set up the test by creating a query with multiple batches"""
        self.statement_list = statement_list = ['select version;', 'select * from t1;']
        self.statement_str = ''.join(statement_list)
        self.query_uri = 'test_uri'
        self.query = Query(self.query_uri, self.statement_str)

        self.mock_query_results = object()
        self.cursor = utils.MockCursor(self.mock_query_results)
        self.connection = utils.MockConnection(cursor=self.cursor)

    def test_query_creates_batches(self):
        """Test that creating a query also creates batches for each statement in the query"""
        # Verify that the query created in setUp has a batch corresponding to each statement
        for index, statement in enumerate(self.statement_list):
            self.assertEqual(self.query.batches[index].batch_text, statement)

    def test_executing_query_executes_batches(self):
        """Test that executing a query also executes all of the query's batches in order"""
        # Set up the query execution callbacks
        callback_before_batch = mock.Mock()
        callback_after_batch = mock.Mock()

        # If I call query.execute
        self.query.execute(self.connection, callback_before_batch, callback_after_batch)

        # Then each of the batches executed in order
        expected_calls = [mock.call(statement) for statement in self.statement_list]
        self.cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(len(self.cursor.execute.mock_calls), 2)

        # And each of the batches holds the expected results
        for batch in self.query.batches:
            self.assertIs(batch.result_set.rows, self.mock_query_results)

        # And the callbacks were executed
        expected_calls = [mock.call(self.query, batch) for batch in self.query.batches]
        callback_before_batch.assert_has_calls(expected_calls)
        self.assertEqual(len(callback_before_batch.mock_calls), 2)
        callback_after_batch.assert_has_calls(expected_calls)
        self.assertEqual(len(callback_after_batch.mock_calls), 2)

        # And the query is marked as executed
        self.assertIs(self.query.execution_state, ExecutionState.EXECUTED)

    def test_batch_failure(self):
        """Test that query execution handles a batch execution failure by stopping further execution"""
        # Set up the query execution callbacks
        callback_before_batch = mock.Mock()
        callback_after_batch = mock.Mock()

        # Set up the cursor to fail when executed
        self.cursor.execute.side_effect = self.cursor.execute_failure_side_effects

        # If I call query.execute then it raises the database error
        with self.assertRaises(psycopg2.DatabaseError):
            self.query.execute(self.connection, callback_before_batch, callback_after_batch)

        # And only the first batch was executed
        expected_calls = [mock.call(self.statement_list[0])]
        self.cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(len(self.cursor.execute.mock_calls), 1)

        # And the callbacks were only executed once
        expected_calls = [mock.call(self.query, self.query.batches[0])]
        callback_before_batch.assert_has_calls(expected_calls)
        self.assertEqual(len(callback_before_batch.mock_calls), 1)
        callback_after_batch.assert_has_calls(expected_calls)
        self.assertEqual(len(callback_after_batch.mock_calls), 1)

        # And the query is marked as executed
        self.assertIs(self.query.execution_state, ExecutionState.EXECUTED)

    def test_batch_selections(self):
        """Test that the query sets up batch objects with correct selection information"""
        full_query = '''select * from
t1;
select * from t2;;;
;  ;
select version(); select * from
t3 ;
select * from t2
'''

        # If I build a query that contains several statements
        query = Query('test_uri', full_query)

        # Then there is a batch for each non-empty statement
        self.assertEqual(len(query.batches), 5)

        # And each batch should have the correct location information
        expected_selections = [(0, 0, 1, 2), (2, 0, 2, 16), (4, 0, 4, 16), (4, 18, 5, 3), (6, 0, 6, 15)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), expected_selections[index])

    def test_batch_selections_do_block(self):
        """Test that the query sets up batch objects with correct selection information for blocks containing statements"""
        full_query = '''DO $$
BEGIN
RAISE NOTICE 'Hello world 1';
RAISE NOTICE 'Hello world 2';
END $$;
select * from t1;'''

        # If I build a query that contains a block that contains several statements
        query = Query('test_uri', full_query)

        # Then there is a batch for each top-level statement
        self.assertEqual(len(query.batches), 2)

        # And each batch should have the correct location information
        expected_selections = [(0, 0, 4, 6), (5, 0, 5, 16)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), expected_selections[index])


def get_execute_string_params() -> ExecuteStringParams:
    """Get a simple ExecutestringParams"""
    params = ExecuteStringParams()
    params.query = 'select version()'
    params.owner_uri = 'test_uri'
    return params


def get_execute_request_params():
    """Get a simple ExecuteRequestParamsBase"""
    params = ExecuteRequestParamsBase()
    params.owner_uri = 'test_uri'
    return params


def _tuple_from_selection_data(data: SelectionData):
    """Convert a SelectionData object to a tuple so that its values can easily be verified"""
    return (data.start_line, data.start_column, data.end_line, data.end_column)


if __name__ == '__main__':
    unittest.main()
