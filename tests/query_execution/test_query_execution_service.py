# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the query execution service"""

import unittest
from unittest import mock

from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration


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


if __name__ == '__main__':
    unittest.main()
