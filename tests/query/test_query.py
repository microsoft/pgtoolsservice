# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import psycopg2

from pgsqltoolsservice.query import ExecutionState, Query, QueryExecutionSettings, QueryEvents
from pgsqltoolsservice.query.contracts import SaveResultsRequestParams, SelectionData, DbColumn
from pgsqltoolsservice.query_execution.contracts import ExecutionPlanOptions
import tests.utils as utils


class TestQuery(unittest.TestCase):
    """Unit tests for Query and Batch objects"""

    def setUp(self):
        """Set up the test by creating a query with multiple batches"""
        self.statement_list = statement_list = ['select version;', 'select * from t1;']
        self.statement_str = ''.join(statement_list)
        self.query_uri = 'test_uri'
        self.query = Query(self.query_uri, self.statement_str, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())

        self.mock_query_results = [('Id1', 'Value1'), ('Id2', 'Value2')]
        self.cursor = utils.MockCursor(self.mock_query_results)
        self.connection = utils.MockConnection(cursor=self.cursor)

        self.columns_info = []
        db_column_id = DbColumn()
        db_column_id.data_type = 'text'
        db_column_id.column_name = 'Id'
        db_column_value = DbColumn()
        db_column_value.data_type = 'text'
        db_column_value.column_name = 'Value'
        self.columns_info = [db_column_id, db_column_value]
        self.get_columns_info_mock = mock.Mock(return_value=self.columns_info)

    def test_query_creates_batches(self):
        """Test that creating a query also creates batches for each statement in the query"""
        # Verify that the query created in setUp has a batch corresponding to each statement
        for index, statement in enumerate(self.statement_list):
            self.assertEqual(self.query.batches[index].batch_text, statement)

    def test_executing_query_executes_batches(self):
        """Test that executing a query also executes all of the query's batches in order"""

        # If I call query.execute
        with mock.patch('pgsqltoolsservice.query.data_storage.storage_data_reader.get_columns_info', new=self.get_columns_info_mock):
            self.query.execute(self.connection)

        # Then each of the batches executed in order
        expected_calls = [mock.call(statement) for statement in self.statement_list]

        self.cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(len(self.cursor.execute.mock_calls), 2)

        # And each of the batches holds the expected results
        for batch in self.query.batches:
            for index in range(0, batch.result_set.row_count):
                current_row = batch.result_set.get_row(index)
                row_tuple = ()
                for cell in current_row:
                    row_tuple += (cell.display_value,)
                self.assertEqual(row_tuple, self.mock_query_results[index])

        # And the query is marked as executed
        self.assertIs(self.query.execution_state, ExecutionState.EXECUTED)

    def test_batch_failure(self):
        """Test that query execution handles a batch execution failure by stopping further execution"""
        # Set up the cursor to fail when executed
        self.cursor.execute.side_effect = self.cursor.execute_failure_side_effects

        # If I call query.execute then it raises the database error
        with self.assertRaises(psycopg2.DatabaseError):
            self.query.execute(self.connection)

        # And only the first batch was executed
        expected_calls = [mock.call(self.statement_list[0])]
        self.cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(len(self.cursor.execute.mock_calls), 1)

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
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())

        # Then there is a batch for each non-empty statement
        self.assertEqual(len(query.batches), 5)

        # And each batch should have the correct location information
        expected_selections = [
            SelectionData(start_line=0, start_column=0, end_line=1, end_column=3),
            SelectionData(start_line=2, start_column=0, end_line=2, end_column=17),
            SelectionData(start_line=4, start_column=0, end_line=4, end_column=17),
            SelectionData(start_line=4, start_column=18, end_line=5, end_column=4),
            SelectionData(start_line=6, start_column=0, end_line=6, end_column=16)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), _tuple_from_selection_data(expected_selections[index]))

    def test_batch_selections_do_block(self):
        """Test that the query sets up batch objects with correct selection information for blocks containing statements"""
        full_query = '''DO $$
BEGIN
RAISE NOTICE 'Hello world 1';
RAISE NOTICE 'Hello world 2';
END $$;
select * from t1;'''

        # If I build a query that contains a block that contains several statements
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())

        # Then there is a batch for each top-level statement
        self.assertEqual(len(query.batches), 2)

        # And each batch should have the correct location information
        expected_selections = [
            SelectionData(start_line=0, start_column=0, end_line=4, end_column=7),
            SelectionData(start_line=5, start_column=0, end_line=5, end_column=17)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), _tuple_from_selection_data(expected_selections[index]))

    def test_batches_strip_comments(self):
        """Test that we do not attempt to execute a batch consisting only of comments"""
        full_query = '''select * from t1;
-- test
-- test
;select * from t1;
-- test
-- test;'''

        # If I build a query that contains a batch consisting of only comments, in addition to other valid batches
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())

        # Then there is only a batch for each non-comment statement
        self.assertEqual(len(query.batches), 2)

        # And each batch should have the correct location information
        expected_selections = [
            SelectionData(start_line=0, start_column=0, end_line=0, end_column=17),
            SelectionData(start_line=3, start_column=1, end_line=3, end_column=18)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), _tuple_from_selection_data(expected_selections[index]))

    def execute_get_subset_raises_error_when_index_not_in_range(self, batch_index: int):
        full_query = 'Select * from t1;'
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())

        with self.assertRaises(IndexError) as context_manager:
            query.get_subset(batch_index, 0, 10)
            self.assertEquals('Batch index cannot be less than 0 or greater than the number of batches', context_manager.exception.args[0])

    def test_get_subset_raises_error_when_index_is_negetive(self):
        self.execute_get_subset_raises_error_when_index_not_in_range(-1)

    def test_get_subset_raises_error_when_index_is_greater_than_batch_size(self):
        self.execute_get_subset_raises_error_when_index_not_in_range(20)

    def test_get_subset(self):
        full_query = 'Select * from t1;'
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions(), None), QueryEvents())
        expected_subset = []

        mock_batch = mock.MagicMock()
        mock_batch.get_subset = mock.Mock(return_value=expected_subset)

        query._batches = [mock_batch]

        subset = query.get_subset(0, 0, 10)

        self.assertEqual(expected_subset, subset)
        mock_batch.get_subset.assert_called_once_with(0, 10)

    def test_save_as_with_invalid_batch_index(self):

        def execute_with_batch_index(index: int):
            params = SaveResultsRequestParams()
            params.batch_index = index

            with self.assertRaises(IndexError) as context_manager:
                self.query.save_as(params, None, None, None)
                self.assertEquals('Batch index cannot be less than 0 or greater than the number of batches', context_manager.exception.args[0])

        execute_with_batch_index(-1)

        execute_with_batch_index(2)

    def test_save_as(self):
        params = SaveResultsRequestParams()
        params.batch_index = 0

        file_factory = mock.MagicMock()
        on_success = mock.MagicMock()
        on_error = mock.MagicMock()

        batch_save_as_mock = mock.MagicMock()
        self.query.batches[0].save_as = batch_save_as_mock

        self.query.save_as(params, file_factory, on_success, on_error)

        batch_save_as_mock.assert_called_once_with(params, file_factory, on_success, on_error)


def _tuple_from_selection_data(data: SelectionData):
    """Convert a SelectionData object to a tuple so that its values can easily be verified"""
    return (data.start_line, data.start_column, data.end_line, data.end_column)


if __name__ == '__main__':
    unittest.main()
