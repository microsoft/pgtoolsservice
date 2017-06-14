# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the query execution service"""

import unittest
import unittest.mock as mock

from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData)
from pgsqltoolsservice.utils import constants


class QueryExecutionServiceTests(unittest.TestCase):
    """Class for testing the query execution service"""

    def test_get_query_full(self):
        """Test getting a query for a URI from the entire file"""
        query_execution_service = QueryExecutionService()
        params = ExecuteStringParams()
        params.query = 'select version()'
        result = query_execution_service._get_query_from_execute_params(params)
        self.assertEqual(result, params.query)

    def test_get_query_selection(self):
        """Test getting a query for a URI from a selection"""
        # Set up the query execution service with a mock workspace service
        query_execution_service = QueryExecutionService()
        query = 'select version()'
        mock_workspace_service = mock.Mock()
        mock_workspace_service.get_text = mock.Mock(return_value=query)
        query_execution_service._service_provider = {constants.WORKSPACE_SERVICE_NAME: mock_workspace_service}

        # Execute the query and verify that the workspace service's get_text method was called
        selection_data = SelectionData()
        selection_data.start_line = 0
        selection_data.start_column = 0
        selection_data.end_line = 0
        selection_data.end_column = 14
        params = ExecuteDocumentSelectionParams()
        params.owner_uri = 'test_uri'
        params.selection_data = selection_data
        result = query_execution_service._get_query_from_execute_params(params)
        mock_workspace_service.get_text.assert_called_once_with(params.owner_uri, selection_data)
        self.assertEqual(result, query)
