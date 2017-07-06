# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test query_execution.Batch"""

from datetime import datetime
import unittest

import psycopg2

from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.contracts.common import SelectionData, BatchSummary, ResultSetSummary  # noqa
from pgsqltoolsservice.query_execution.result_set import ResultSet
import tests.utils as utils


class TestBatch(unittest.TestCase):
    """Methods for testing the batch class"""

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.default_sel_data = None

    def setUp(self):
        """Constructor"""
        self.default_sel_data = SelectionData()
        self.batch = Batch('', 0, self.default_sel_data)
        self.mock_cursor = utils.MockCursor(None)
        self.mock_cursor.rowcount = 5

    def test_build_batch_summary(self):
        """Test that the proper Batch Summary format is created"""
        batch_summary: BatchSummary = self.batch.build_batch_summary()
        self.assertEqual(batch_summary.id, 0)
        self.assertEqual(batch_summary.selection, self.default_sel_data)
        self.assertFalse(batch_summary.has_error)
        self.assertIsNotNone(batch_summary.execution_start)
        self.assertIsNone(batch_summary.execution_end)
        self.assertIsNone(batch_summary.result_set_summaries)
        self.assertIsNone(batch_summary.special_action)
        self.assertIsNone(batch_summary.execution_elapsed)

        # Check batch summary parameters after batch has executed,
        # a result set has been added, and
        # we re-call build batch summary
        self.batch.has_executed = True
        self.batch.end_time = datetime.now()
        self.batch.result_set = ResultSet()
        batch_summary = self.batch.build_batch_summary()
        self.assertEqual(batch_summary.id, 0)
        self.assertEqual(batch_summary.selection, self.default_sel_data)
        self.assertFalse(batch_summary.has_error)
        self.assertIsNotNone(batch_summary.execution_start)
        self.assertIsNotNone(batch_summary.execution_end)
        self.assertIsNotNone(batch_summary.execution_elapsed)
        self.assertIsNotNone(batch_summary.result_set_summaries)
        self.assertTrue(isinstance(batch_summary.result_set_summaries[0], ResultSetSummary))
        self.assertIsNone(batch_summary.special_action)

    def test_batch_execution_updates_batch(self):
        """Test that executing a batch updates the batch's details"""
        # If I execute a batch
        self.batch.execute(self.mock_cursor)

        # Then the batch's details have been updated
        self.assertFalse(self.batch.has_error)
        self.assertTrue(self.batch.has_executed)
        self.assertIsNotNone(self.batch.result_set)
        self.assertGreaterEqual(self.batch.end_time, self.batch.start_time)
        self.assertEqual(self.batch.row_count, self.mock_cursor.rowcount)
        self.assertGreater(len(self.batch.notices), 0)

        # And the connection's notices were cleared
        self.assertEqual(self.mock_cursor.connection.notices, [])

    def test_batch_execution_failure_updates_batch(self):
        """Test that executing a batch updates the batch's details if execution fails"""
        # Set up the cursor to fail when executing
        self.mock_cursor.execute.side_effect = self.mock_cursor.execute_failure_side_effects

        # If I execute a batch, then it raises the database error
        with self.assertRaises(psycopg2.DatabaseError):
            self.batch.execute(self.mock_cursor)

        # And the batch's details have been updated
        self.assertTrue(self.batch.has_error)
        self.assertTrue(self.batch.has_executed)
        self.assertIsNone(self.batch.result_set)
        self.assertGreaterEqual(self.batch.end_time, self.batch.start_time)
        self.assertEqual(self.batch.row_count, -1)
        self.assertGreater(len(self.batch.notices), 0)

        # And the connection's notices were cleared
        self.assertEqual(self.mock_cursor.connection.notices, [])


if __name__ == '__main__':
    unittest.main()
