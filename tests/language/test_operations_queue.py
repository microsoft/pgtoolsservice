# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import threading    # noqa
from typing import List, Tuple, Optional
import unittest
from unittest import mock

from tests.utils import MockConnection
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

    def test_add_none_operation_throws(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        with self.assertRaises(ValueError):
            operations_queue.add_operation(None)

    def test_add_operation_without_context_throws(self):
        operations_queue = OperationsQueue(self.mock_service_provider)
        with self.assertRaises(KeyError):
            operations_queue.add_operation(QueuedOperation('something', None, None))

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
        connect_result = mock.MagicMock()
        connect_result.error_message = None
        self.mock_connection_service.get_connection = mock.Mock(return_value=mock.MagicMock())
        self.mock_connection_service.connect = mock.MagicMock(return_value=connect_result)

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

    def test_add_same_context_twice_with_overwrite_creates_two_contexts(self):
        connect_result = mock.MagicMock()
        connect_result.error_message = None
        self.mock_connection_service.get_connection = mock.Mock(return_value=mock.MagicMock())
        self.mock_connection_service.connect = mock.MagicMock(return_value=connect_result)
        self.mock_connection_service.disconnect = mock.MagicMock(return_value=True)

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


class TestConnectionContextQueue(unittest.TestCase):
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