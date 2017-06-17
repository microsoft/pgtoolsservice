# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the query execution service"""

import unittest
from unittest import mock

import psycopg2

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
import tests.utils as utils


class TestQueryService(unittest.TestCase):
    """Methods for testing the query execution service"""

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
        params = ExecuteStringParams()
        params.query = 'select version()'
        params.owner_uri = 'invalid_uri'

        # If I try to handle a query request with an invalid owner URI
        query_execution_service._handle_execute_query_request(mock_request_context, params)

        # Then it responds with an error instead of a regular response
        mock_request_context.send_error.assert_called_once()
        mock_request_context.send_response.assert_not_called()

    def test_query_request_error_handline(self):
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
        params = ExecuteStringParams()
        params.query = 'select version()'
        params.owner_uri = 'test_uri'

        # If I handle a query that raises an error when executed
        query_execution_service._handle_execute_query_request(mock_request_context, params)

        # Then the transaction gets rolled back and the cursor gets closed
        mock_connection.rollback.assert_called_once()
        mock_connection.commit.assert_not_called()
        mock_cursor.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
