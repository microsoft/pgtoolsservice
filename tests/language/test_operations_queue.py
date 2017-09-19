# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import threading    # noqa
from typing import Callable, List, Optional, Tuple  # noqa
import unittest
from unittest import mock

from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.connection.contracts import ConnectionDetails, ConnectRequestParams  # noqa
from pgsqltoolsservice.connection import ConnectionService, ConnectionInfo
from pgsqltoolsservice.language.operations_queue import (
    ConnectionContext, OperationsQueue, QueuedOperation, INTELLISENSE_URI
)

COMPLETIONREFRESHER_PATH_PATH = 'pgsqltoolsservice.language.operations_queue.CompletionRefresher'


class TestOperationsQueue(unittest.TestCase):
    """Methods for testing the OperationsQueue"""

    def setUp(self):
        """Constructor"""
        self.default_connection_key = 'server_db_user'
        self.mock_connection_service = ConnectionService()
        self.mock_server = JSONRPCServer(None, None)
        self.mock_service_provider = ServiceProvider(self.mock_server, {}, None)
        self.mock_service_provider._services[constants.CONNECTION_SERVICE_NAME] = self.mock_connection_service
        self.mock_service_provider._is_initialized = True

        # Create connection information for use in the tests
        self.connection_details = ConnectionDetails.from_data({})
        self.connection_details.server_name = 'test_host'
        self.connection_details.database_name = 'test_db'
        self.connection_details.user_name = 'user'
        self.expected_context_key = 'test_host|test_db|user'
        self.expected_connection_uri = INTELLISENSE_URI + self.expected_context_key
        self.test_uri = 'test_uri'
        self.connection_info = ConnectionInfo(self.test_uri, self.connection_details)

        # Create mock CompletionRefresher to avoid calls to create separate thread
        self.refresher_mock = mock.MagicMock()
        self.refresh_method_mock = mock.MagicMock()
        self.refresher_mock.refresh = self.refresh_method_mock

    def test_init(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        self.assertFalse(operations_queue.stop_requested)
        self.assertTrue(operations_queue.queue.empty)

    def test_start_process_stop(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        operations_queue.start()
        self.assertTrue(operations_queue._operations_consumer.isAlive())
        operations_queue.stop()
        operations_queue._operations_consumer.join(2)
        self.assertFalse(operations_queue._operations_consumer.isAlive())

    def test_add_context_creates_new_context(self):
        # Given a connection will be created on a connect request
        connect_result = mock.MagicMock()
        connect_result.error_message = None
        self.mock_connection_service.get_connection = mock.Mock(return_value=mock.MagicMock())
        self.mock_connection_service.connect = mock.MagicMock(return_value=connect_result)

        # When I add a connection context
        operations_queue = OperationsQueue(self.mock_service_provider)

        with mock.patch(COMPLETIONREFRESHER_PATH_PATH) as refresher_patch:
            refresher_patch.return_value = self.refresher_mock
            context: ConnectionContext = operations_queue.add_connection_context(self.connection_info)
            # Then I expect the context to be non-null
            self.assertIsNotNone(context)
            self.assertEqual(context.key, self.expected_context_key)
            self.assertFalse(context.intellisense_complete.is_set())
            self.assertTrue(operations_queue.has_connection_context(self.connection_info))

    def test_add_same_context_twice_creates_one_context(self):
        def do_test():
            # When I add context for 2 URIs with same connection details
            operations_queue = OperationsQueue(self.mock_service_provider)

            with mock.patch(COMPLETIONREFRESHER_PATH_PATH) as refresher_patch:
                refresher_patch.return_value = self.refresher_mock
                operations_queue.add_connection_context(self.connection_info)
                conn_info2 = ConnectionInfo('newuri', self.connection_info.details)
                operations_queue.add_connection_context(conn_info2)
                # Then I expect to only have connection
                connect_mock: mock.MagicMock = self.mock_connection_service.connect
                connect_mock.assert_called_once()
                connect_params: ConnectRequestParams = connect_mock.call_args[0][0]
                self.assertEqual(connect_params.owner_uri, self.expected_connection_uri)
        self._run_with_mock_connection(do_test)

    def test_add_same_context_twice_with_overwrite_creates_two_contexts(self):
        def do_test():
            # When I add context for 2 URIs with same connection details
            operations_queue = OperationsQueue(self.mock_service_provider)
            with mock.patch(COMPLETIONREFRESHER_PATH_PATH) as refresher_patch:
                refresher_patch.return_value = self.refresher_mock
                operations_queue.add_connection_context(self.connection_info)
                conn_info2 = ConnectionInfo('newuri', self.connection_info.details)
                operations_queue.add_connection_context(conn_info2, overwrite=True)
                # Then I expect to only have 1 connection
                # and I expect disconnect and reconnect to have been called
                connect_mock: mock.MagicMock = self.mock_connection_service.connect
                self.assertEqual(connect_mock.call_count, 2)
                self.assertEqual(connect_mock.call_args_list[0][0][0].owner_uri, self.expected_connection_uri)
                self.assertEqual(connect_mock.call_args_list[1][0][0].owner_uri, self.expected_connection_uri)
                disconnect_mock: mock.MagicMock = self.mock_connection_service.disconnect
                disconnect_mock.assert_called_once()
        self._run_with_mock_connection(do_test)

    def test_add_none_operation_throws(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        with self.assertRaises(ValueError):
            operations_queue.add_operation(None)

    def test_add_operation_without_context_throws(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        with self.assertRaises(KeyError):
            operations_queue.add_operation(QueuedOperation('something', None, None))

    def test_add_operation_succeeds_when_has_key(self):
        # Given I have a connection in the map
        operations_queue = OperationsQueue(self.mock_service_provider)
        operations_queue._context_map[self.expected_context_key] = ConnectionContext(self.expected_context_key)
        # When I add an operation
        operations_queue.add_operation(QueuedOperation(self.expected_context_key, None, None))
        # Then I expect the operation to be added successfully to the queue
        operation: QueuedOperation = operations_queue.queue.get_nowait()
        self.assertEqual(operation.key, self.expected_context_key)
        # ... and I expect the context to have been set automatically
        self.assertEqual(operation.context, operations_queue._context_map[self.expected_context_key])

    def test_execute_operation_ignores_none_param(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        try:
            operations_queue.execute_operation(None)
        except Exception as e:
            self.fail(e)

    def test_execute_operation_calls_timeout_if_not_connected(self):
        # Given an operation with a non-connected context
        task = mock.Mock()
        timeout_task = mock.Mock()
        operations_queue = OperationsQueue(self.mock_service_provider)
        operation = QueuedOperation(self.expected_context_key, task, timeout_task)
        operation.context = ConnectionContext(self.expected_context_key)
        # When I execute the operation
        operations_queue.execute_operation(operation)
        # Then I expect the timeout task to be called
        timeout_task.assert_called_once()
        # ... and I do not expect the regular task to be called
        task.assert_not_called()

    def test_execute_operation_calls_task_if_connected(self):
        # Given an operation with a connected context
        context = ConnectionContext(self.expected_context_key)
        context.is_connected = True
        context.pgcompleter = mock.Mock()
        task = mock.MagicMock(return_value=True)
        timeout_task = mock.Mock()
        operations_queue = OperationsQueue(self.mock_service_provider)
        operation = QueuedOperation(self.expected_context_key, task, timeout_task)
        operation.context = context
        # When I execute the operation
        operations_queue.execute_operation(operation)
        # Then I expect the regular task to be called
        task.assert_called_once()
        actual_context = task.call_args[0][0]
        self.assertEqual(actual_context, context)
        # ... and I do not expect the timeout task to be called
        timeout_task.assert_not_called()

    def test_execute_operation_calls_task_and_timouttask_if_task_fails(self):
        # Given an operation where the task will fail (return false)
        context = ConnectionContext(self.expected_context_key)
        context.is_connected = True
        context.pgcompleter = mock.Mock()
        task = mock.MagicMock(return_value=False)
        timeout_task = mock.Mock()
        operations_queue = OperationsQueue(self.mock_service_provider)
        operation = QueuedOperation(self.expected_context_key, task, timeout_task)
        operation.context = context
        # When I execute the operation
        operations_queue.execute_operation(operation)
        # Then I expect the regular task to be called
        task.assert_called_once()
        actual_context = task.call_args[0][0]
        self.assertEqual(actual_context, context)
        # ... and I also expect the timeout task to be called
        timeout_task.assert_called_once()

    # HELPER METHODS ###############################################
    def _run_with_mock_connection(self, test: Callable[[None], None]):
        connect_result = mock.MagicMock()
        connect_result.error_message = None
        self.mock_connection_service.get_connection = mock.Mock(return_value=mock.MagicMock())
        self.mock_connection_service.connect = mock.MagicMock(return_value=connect_result)
        self.mock_connection_service.disconnect = mock.MagicMock(return_value=True)
        test()


class TestConnectionContextQueue(unittest.TestCase):
    """Methods for testing the OperationsQueue"""

    def setUp(self):
        # Create connection information for use in the tests
        self.expected_context_key = 'test_host|test_db|user'
        self.expected_connection_uri = INTELLISENSE_URI + self.expected_context_key

        # Create mock CompletionRefresher to avoid calls to create separate thread
        self.refresher_mock = mock.MagicMock()
        self.refresh_method_mock = mock.MagicMock()
        self.refresher_mock.refresh = self.refresh_method_mock

    def test_init(self):
        connection_context = ConnectionContext(self.expected_context_key)
        self.assertEqual(connection_context.key, self.expected_context_key)
        self.assertFalse(connection_context.intellisense_complete.is_set())
        self.assertIsNone(connection_context.pgcompleter)
        self.assertFalse(connection_context.is_connected)

    def test_on_completions_refreshed(self):
        connection = mock.Mock()

        def do_test():
            # When I call refresh_metadata and refresh completes
            connection_context = ConnectionContext(self.expected_context_key)
            connection_context.refresh_metadata(connection)
            completer = mock.Mock()
            self._complete_refresh(completer)
            # Then the completer object should be saved and an event raised
            self.assertEqual(connection_context.pgcompleter, completer)
            self.assertTrue(connection_context.is_connected)
            self.assertTrue(connection_context.intellisense_complete.is_set())
        self._run_with_mock_refresher(do_test)

    def _complete_refresh(self, completer):
        callback = self.refresh_method_mock.call_args[0][0]
        self.assertIsNotNone(callback)
        callback(completer)

    def _run_with_mock_refresher(self, test: Callable[[None], None]):
        with mock.patch(COMPLETIONREFRESHER_PATH_PATH) as refresher_patch:
            refresher_patch.return_value = self.refresher_mock
            test()
