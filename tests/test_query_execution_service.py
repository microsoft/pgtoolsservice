# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test query_execution.QueryExecutionService"""

import unittest
import mock

from pgsqltoolsservice.query_execution.query_execution_service import QueryExecutionService
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.query_execution.contracts.common import DbColumn, ResultSetSubset
import pgsqltoolsservice.utils as utils


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

    def test_result_set_subset_positive(self):
        """
        Test for proper generation of ResultSetSubset
        that is part of query/subset response payload
        """
        query_results = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        results_size = len(query_results)
        row_size = 3
        result_set_subset = ResultSetSubset(query_results, 0, results_size)
        self.assertEquals(results_size, result_set_subset.row_count)
        db_cell_values = result_set_subset.rows
        values_len = len(db_cell_values)
        self.assertEqual(values_len, results_size)

        #Check that the DbColumn[][] is generated correctly
        row_index = 0
        column_index = 0
        for row_index in range(0, values_len):
            row_len = len(db_cell_values[row_index])
            self.assertEqual(row_len, row_size)
            row = db_cell_values[row_index]
            for column_index in range(0, row_len):
                result_cell = query_results[row_index][column_index]
                cell = row[column_index]
                self.assertEqual(cell.display_value, None if result_cell is None else str(result_cell))
                self.assertEqual(cell.is_null, result_cell is None)
                self.assertEqual(cell.row_id, row_index)
    
    def test_result_set_subset_negative(self):
        """
        Test that we properly raise an error if our indices are
        out of range
        """
        query_results = [("Result1", 53, 2.57), ("Result2", None, "foobar")]
        results_size = len(query_results)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, -1, results_size)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, 0, results_size + 1)
        with self.assertRaises(ValueError):
            ResultSetSubset(query_results, -1, 0)

    def test_result_set_positive(self):
        """Test that we properly generate the result set"""
        description = [("first", 0, 1, 2, 3, 4, True), ("second", 5, 6, 7, 8, 9, False)]
        test_columns = [DbColumn(0, description[0]), DbColumn(1, description[1])]
        ordinal = 0
        batch_ordinal = 0
        row_count = len(description)

        result_set = ResultSet(ordinal, batch_ordinal, description, row_count)
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
    
    def test_result_set_column_none_description(self):
        """Test that result set column is empty if description is None.
        Description is None if there were no results for a query
        """
        description = None
        result_set = ResultSet(0, 0, description, 0)
        self.assertEqual([], result_set.columns)



if __name__ == '__main__':
    unittest.main()
