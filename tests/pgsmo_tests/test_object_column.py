# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.column.column import Column
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

COLUMN_ROW = {
    'name': 'abc',
    'datatype': 'character',
    'oid': 123,
    'has_default_val': True,
    'not_null': True
}


class TestColumn(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = [
            'has_default_value', '_has_default_value',
            'not_null', '_not_null'
        ]
        colls = []
        name = 'column'
        datatype = 'character'
        mock_conn = ServerConnection(utils.MockConnection(None))
        obj = Column(mock_conn, name, datatype)
        utils.validate_init(
            Column, name, mock_conn, obj, props, colls,
            lambda obj: self._validate_init(obj, datatype)
        )

    def test_from_node_query(self):
        utils.from_node_query_base(Column, COLUMN_ROW, self._validate_column)

    def test_get_nodes_for_parent(self):
        # Use the test helper for this method
        get_nodes_for_parent = (lambda conn: Column.get_nodes_for_parent(conn, 10))
        utils.get_nodes_for_parent_base(Column, COLUMN_ROW, get_nodes_for_parent, self._validate_column)

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_init(self, obj: Column, datatype: str):
        self.assertEqual(obj._datatype, datatype)
        self.assertEqual(obj.datatype, datatype)

    def _validate_column(self, obj: Column, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, COLUMN_ROW['oid'])
        self.assertEqual(obj.oid, COLUMN_ROW['oid'])
        self.assertEqual(obj._name, COLUMN_ROW['name'])
        self.assertEqual(obj.name, COLUMN_ROW['name'])

        # Column-specific basic properties
        self.assertEqual(obj._datatype, COLUMN_ROW['datatype'])
        self.assertEqual(obj.datatype, COLUMN_ROW['datatype'])
        self.assertEqual(obj._has_default_value, COLUMN_ROW['has_default_val'])
        self.assertEqual(obj.has_default_value, COLUMN_ROW['has_default_val'])
        self.assertEqual(obj._not_null, COLUMN_ROW['not_null'])
        self.assertEqual(obj.not_null, COLUMN_ROW['not_null'])