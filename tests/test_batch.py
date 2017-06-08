# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import unittest
from nose.tools import with_setup
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.contracts.common import (SelectionData, BatchSummary)

class TestBatch(unittest.TestCase):
    """Methods for testing the batch class"""
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.default_sel_data = None

    def setup(self):
        """Constructor"""
        self.default_sel_data = SelectionData(0, 0, 1, 1)

    @with_setup(setup)
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

if __name__ == '__main__':
    unittest.main()
