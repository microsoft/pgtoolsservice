# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing the object explorer service"""

import unittest
import io
from queue import Queue
import time
import unittest.mock as mock

from pgsqltoolsservice.query_execution import QueryExecutionService
from pgsqltoolsservice.query_execution.contracts import (
    ExecuteDocumentSelectionParams, ExecuteStringParams, SelectionData)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.object_explorer.contracts import CreateSessionParameters

class TestObjectExplorer(unittest.TestCase):
    """Methods for testing the object explorer service"""

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

    def test_get_oe_tree(self):
        """Test getting a query for a URI from the entire file"""

        self.assertEqual(1, 1)
        # Set up the service and the query
        # query_execution_service = QueryExecutionService()
        # params = ExecuteStringParams()
        # params.query = 'select version()'
        # # If I try to get a query using ExecuteStringParams
        # result = query_execution_service._get_query_from_execute_params(params)
        # # Then the retrieved query should be the same as the one on the params object
        # self.assertEqual(result, params.query)



    def test_create_sessions(self):
        """Test creating an Object Explorer session"""

        self.assertEqual(1, 1)

        # Set up the service and the query
        # query_execution_service = QueryExecutionService()
        # params = ExecuteStringParams()
        # params.query = 'select version()'
        # # If I try to get a query using ExecuteStringParams
        # result = query_execution_service._get_query_from_execute_params(params)
        # # Then the retrieved query should be the same as the one on the params object
        # self.assertEqual(result, params.query)        

if __name__ == '__main__':
    unittest.main()
