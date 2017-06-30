# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test query_execution.Batch"""

import unittest
from datetime import datetime

from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.result_set import ResultSet
from pgsqltoolsservice.query_execution.contracts.common import SelectionData, BatchSummary, ResultSetSummary  # noqa


class TestBatch(unittest.TestCase):
    """Methods for testing the batch class"""

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.default_sel_data = None

    def setUp(self):
        """Constructor"""
        self.default_sel_data = SelectionData()

    def test_build_batch_summary(self):
        """Test that the proper Batch Summary format is created"""
        batch = Batch(0, self.default_sel_data, False)

        batch_summary: BatchSummary = batch.build_batch_summary()
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
        batch.has_executed = True
        batch.end_time = datetime.now()
        batch.result_sets.append(ResultSet())
        batch_summary = batch.build_batch_summary()
        self.assertEqual(batch_summary.id, 0)
        self.assertEqual(batch_summary.selection, self.default_sel_data)
        self.assertFalse(batch_summary.has_error)
        self.assertIsNotNone(batch_summary.execution_start)
        self.assertIsNotNone(batch_summary.execution_end)
        self.assertIsNotNone(batch_summary.execution_elapsed)
        self.assertIsNotNone(batch_summary.result_set_summaries)
        self.assertTrue(isinstance(batch_summary.result_set_summaries[0], ResultSetSummary))
        self.assertIsNone(batch_summary.special_action)


if __name__ == '__main__':
    unittest.main()
