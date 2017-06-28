# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test query_execution.Batch"""

import unittest
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.contracts.common import SelectionData, BatchSummary  # noqa


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
        batch = Batch('', 0, self.default_sel_data)

        batch_summary: BatchSummary = batch.build_batch_summary()
        self.assertEqual(batch_summary.id, 0)
        self.assertEqual(batch_summary.selection, self.default_sel_data)
        self.assertFalse(batch_summary.has_error)
        self.assertIsNotNone(batch_summary.execution_start)
        self.assertIsNone(batch_summary.execution_end)
        self.assertIsNone(batch_summary.result_set_summaries)
        self.assertIsNone(batch_summary.special_action)


if __name__ == '__main__':
    unittest.main()
