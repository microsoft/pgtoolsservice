# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test query_execution.QueryExecutionService"""

import unittest
import mock

from pgsqltoolsservice.query_execution.query_execution_service import QueryExecutionService
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.query_execution.contracts.common import SelectionData, DbColumn


class TestQueryService(unittest.TestCase):
    """Methods for testing the query execution service"""

    def test_initialization(self):
        # Setup: Create a capabilities service with a mocked out service provider
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
            self.assertIsInstance(mock_call[1][0], IncomingMessageConfiguration)
            self.assertTrue(callable(mock_call[1][1]))
    

    def test_db_cell_values(self):
        """
        Test for proper generation of DbCellValue[][] 
        that is part of query/subset response payload
        """
        service = QueryExecutionService()
        service.query_results = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        RESULTS_SIZE = len(service.query_results)
        ROW_SIZE = 3
        db_cell_values = service.build_db_cell_values(service.query_results, 0, RESULTS_SIZE)
        self.assertEqual(len(db_cell_values), RESULTS_SIZE)

        row_index = 0
        column_index = 0
        for row in db_cell_values:
            self.assertEqual(len(row), ROW_SIZE)
            for cell in row:
                result_cell = service.query_results[row_index][column_index]
                self.assertEqual(cell.display_value, str(result_cell))
                self.assertEqual(cell.is_null, result_cell is None)
                self.assertEqual(cell.row_id, row_index)
                column_index += 1
            column_index = 0
            row_index += 1


    def test_generate_column_info(self):
        """Test generate_batch_event_params function"""
        service = QueryExecutionService()
        description = [("first", 0, 1, 2, 3, 4, True), ("second", 5, 6, 7, 8, 9, False)]
        test_columns = [DbColumn(0, description[0]), DbColumn(1, description[1])]
        generated_columns = service.generate_column_info(description)
        self.assertEqual(len(test_columns), len(generated_columns))
        
        index = 0
        for column in test_columns:
            self.assertEqual(column.__dict__, generated_columns[index].__dict__)
            index += 1

if __name__ == '__main__':
    unittest.main()
