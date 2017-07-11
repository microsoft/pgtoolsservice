# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.table.table import Table
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

TABLE_ROW = {
    'name': 'tablename',
    'oid': 123
}


class TestTable(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = []
        colls = ['_columns', 'columns']
        utils.init_base(Table, props, colls)

    def test_from_node_query(self):
        utils.from_node_query_base(Table, TABLE_ROW, self._validate_table)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Table,
            TABLE_ROW,
            lambda conn: Table.get_nodes_for_parent(conn, 0),
            self._validate_table
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_table(self, table: Table, mock_conn: ServerConnection):
        utils.validate_node_object_props(table, mock_conn, TABLE_ROW['name'], TABLE_ROW['oid'])

        # Child objects
        self.assertIsInstance(table._columns, NodeCollection)
        self.assertIs(table.columns, table._columns)
