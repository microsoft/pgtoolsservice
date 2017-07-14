# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects.column import Column
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestColumn(NodeObjectTestBase, unittest.TestCase):
    NODE_QUERY = {
        'name': 'abc',
        'datatype': 'character',
        'oid': 123,
        'has_default_val': True,
        'not_null': True
    }

    @property
    def class_for_test(self):
        return Column

    @property
    def basic_properties(self):
        return {
            'has_default_value': self.node_query['has_default_val'],
            '_has_default_value': self.node_query['has_default_val'],
            'not_null': self.node_query['not_null'],
            '_not_null': self.node_query['not_null']
        }

    @property
    def collections(self):
        return []

    @property
    def node_query(self):
        return TestColumn.NODE_QUERY

    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        """Tests __init__, overrides default test b/c column init takes additional param"""
        # If: I create an instance of the Column class
        name = 'column'
        datatype = 'character'
        mock_conn = ServerConnection(utils.MockConnection(None))
        obj = Column(mock_conn, name, datatype)

        # Then:
        # ... The standard object tests should pass
        self._init_validation(obj, mock_conn, name)

        # ... The datatype property should be set
        self.assertEqual(obj.datatype, datatype)
        self.assertEqual(obj._datatype, datatype)

