# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

from __future__ import unicode_literals

import unittest
from nose.tools import with_setup
from pgsqltoolsservice.query_execution.batch import Batch
from pgsqltoolsservice.query_execution.selection_data import SelectionData
from pgsqltoolsservice.query_execution.batch_summary import BatchSummary



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
        self.assertFalse(batch_summary.hasError)
        self.assertIsNotNone(batch_summary.executionStart)
        self.assertIsNone(batch_summary.executionEnd)
        self.assertIsNone(batch_summary.resultSetSummaries)
        self.assertIsNone(batch_summary.specialAction)

if __name__ == '__main__':
    unittest.main()
