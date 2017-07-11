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
        colls = [
            '_check_constraints', 'check_constraints',
            '_columns', 'columns',
            '_exclusion_constraints', 'exclusion_constraints',
            '_foreign_key_constraints', 'foreign_key_constraints',
            '_index_constraints', 'index_constraints',
            '_indexes', 'indexes',
            '_rules', 'rules',
            '_triggers', 'triggers'
        ]
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

    # METHOD TESTS #########################################################
    def test_refresh(self):
        # Setup: Create a table object and mock up the node collection reset method
        mock_conn = ServerConnection(utils.MockConnection(None))
        table = Table._from_node_query(mock_conn, **TABLE_ROW)
        table._check_constraints.reset = mock.MagicMock()
        table._columns.reset = mock.MagicMock()
        table._exclusion_constraints.reset = mock.MagicMock()
        table._foreign_key_constraints.reset = mock.MagicMock()
        table._index_constraints.reset = mock.MagicMock()
        table._indexes.reset = mock.MagicMock()
        table._rules.reset = mock.MagicMock()
        table._triggers.reset = mock.MagicMock()

        # If: I refresh a table object
        table.refresh()

        # Then: The child object node collections should have been reset
        table._check_constraints.reset.assert_called_once()
        table._columns.reset.assert_called_once()
        table._exclusion_constraints.reset.assert_called_once()
        table._foreign_key_constraints.reset.assert_called_once()
        table._index_constraints.reset.assert_called_once()
        table._indexes.reset.assert_called_once()
        table._rules.reset.assert_called_once()
        table._triggers.reset.assert_called_once()

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_table(self, table: Table, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(table._conn, mock_conn)
        self.assertEqual(table._oid, TABLE_ROW['oid'])
        self.assertEqual(table.oid, TABLE_ROW['oid'])
        self.assertEqual(table._name, TABLE_ROW['name'])
        self.assertEqual(table.name, TABLE_ROW['name'])

        # Child objects
        self.assertIsInstance(table._check_constraints, NodeCollection)
        self.assertIs(table.check_constraints, table._check_constraints)
        self.assertIsInstance(table._columns, NodeCollection)
        self.assertIs(table.columns, table._columns)
        self.assertIsInstance(table._exclusion_constraints, NodeCollection)
        self.assertIs(table.exclusion_constraints, table._exclusion_constraints)
        self.assertIsInstance(table._foreign_key_constraints, NodeCollection)
        self.assertIs(table.foreign_key_constraints, table._foreign_key_constraints)
        self.assertIsInstance(table._index_constraints, NodeCollection)
        self.assertIs(table.index_constraints, table._index_constraints)
        self.assertIsInstance(table._indexes, NodeCollection)
        self.assertIs(table.indexes, table._indexes)
        self.assertIsInstance(table._rules, NodeCollection)
        self.assertIs(table.rules, table._rules)
        self.assertIsInstance(table._triggers, NodeCollection)
        self.assertIs(table.triggers, table._triggers)
