# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.column.column import Column
import tests.pgsmo_tests.utils as utils

COLUMN_ROW = {
    'name': 'abc',
    'datatype': 'character',
    'oid': 123,
    'has_default_val': True,
    'not_null': True
}


class TestColumn(unittest.TestCase):
    def test_init(self):
        # If: I create a new column object
        mock_conn = {}
        mock_name = 'abc'
        mock_datatype = 'character'
        col = Column(mock_conn, mock_name, mock_datatype)

        # Then:
        # ... The column should be an instance of a node object
        self.assertIsInstance(col, NodeObject)

        # ... All the properties should be assigned properly
        self.assertEqual(col._oid, None)
        self.assertEqual(col.oid, None)
        self.assertEqual(col._name, mock_name)
        self.assertEqual(col.name, mock_name)
        self.assertEqual(col._datatype, mock_datatype)
        self.assertEqual(col.datatype, mock_datatype)
        self.assertIsNone(col._has_default_value)
        self.assertIsNone(col.has_default_value)
        self.assertIsNone(col._not_null)
        self.assertIsNone(col.not_null)

    def test_from_node_query(self):
        # If: I create a column from a node query
        mock_conn = {}
        col = Column._from_node_query(mock_conn, **COLUMN_ROW)

        # Then:
        # ... The returned column must be a column
        self.assertIsInstance(col, NodeObject)
        self.assertIsInstance(col, Column)

        self._validate_column(col)

    def test_get_nodes_for_parent(self):
        # Use the test helper for this method
        get_nodes_for_parent = (lambda conn: Column.get_nodes_for_parent(conn, 10))
        utils.get_nodes_for_parent_base(Column, COLUMN_ROW, get_nodes_for_parent, self._validate_column)

    def _validate_column(self, obj: Column):
        # ... All properties should be assigned properly
        self.assertEqual(obj._oid, COLUMN_ROW['oid'])
        self.assertEqual(obj.oid, COLUMN_ROW['oid'])
        self.assertEqual(obj._name, COLUMN_ROW['name'])
        self.assertEqual(obj.name, COLUMN_ROW['name'])
        self.assertEqual(obj._datatype, COLUMN_ROW['datatype'])
        self.assertEqual(obj.datatype, COLUMN_ROW['datatype'])
        self.assertEqual(obj._has_default_value, COLUMN_ROW['has_default_val'])
        self.assertEqual(obj.has_default_value, COLUMN_ROW['has_default_val'])
        self.assertEqual(obj._not_null, COLUMN_ROW['not_null'])
        self.assertEqual(obj.not_null, COLUMN_ROW['not_null'])