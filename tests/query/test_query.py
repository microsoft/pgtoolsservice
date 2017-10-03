# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import psycopg2

from pgsqltoolsservice.query import ExecutionState, Query, QueryExecutionSettings, QueryEvents
from pgsqltoolsservice.query.contracts import SelectionData
from pgsqltoolsservice.query_execution.contracts import ExecutionPlanOptions
import tests.utils as utils


class TestQuery(unittest.TestCase):
    """Unit tests for Query and Batch objects"""

    def setUp(self):
        """Set up the test by creating a query with multiple batches"""
        self.statement_list = statement_list = ['select version;', 'select * from t1;']
        self.statement_str = ''.join(statement_list)
        self.query_uri = 'test_uri'
        self.query = Query(self.query_uri, self.statement_str, QueryExecutionSettings(ExecutionPlanOptions()), QueryEvents())

        self.mock_query_results = [('True'), ('False')]
        self.cursor = utils.MockCursor(self.mock_query_results)
        self.connection = utils.MockConnection(cursor=self.cursor)

    def test_query_creates_batches(self):
        """Test that creating a query also creates batches for each statement in the query"""
        # Verify that the query created in setUp has a batch corresponding to each statement
        for index, statement in enumerate(self.statement_list):
            self.assertEqual(self.query.batches[index].batch_text, statement)

    def test_executing_query_executes_batches(self):
        """Test that executing a query also executes all of the query's batches in order"""

        # If I call query.execute
        self.query.execute(self.connection)

        # Then each of the batches executed in order
        expected_calls = [mock.call(statement) for statement in self.statement_list]
        self.cursor.execute.assert_has_calls(expected_calls)
        self.assertEqual(len(self.cursor.execute.mock_calls), 2)

        # And each of the batches holds the expected results
        for batch in self.query.batches:
            self.assertEqual(batch.result_set.rows, self.mock_query_results)

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
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions()), QueryEvents())

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
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions()), QueryEvents())

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
        query = Query('test_uri', full_query, QueryExecutionSettings(ExecutionPlanOptions()), QueryEvents())

        # Then there is only a batch for each non-comment statement
        self.assertEqual(len(query.batches), 2)

        # And each batch should have the correct location information
        expected_selections = [
            SelectionData(start_line=0, start_column=0, end_line=0, end_column=17),
            SelectionData(start_line=3, start_column=1, end_line=3, end_column=18)]
        for index, batch in enumerate(query.batches):
            self.assertEqual(_tuple_from_selection_data(batch.selection), _tuple_from_selection_data(expected_selections[index]))


def _tuple_from_selection_data(data: SelectionData):
    """Convert a SelectionData object to a tuple so that its values can easily be verified"""
    return (data.start_line, data.start_column, data.end_line, data.end_column)
