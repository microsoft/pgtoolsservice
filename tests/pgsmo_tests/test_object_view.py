# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.view.view import View
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'viewname',
    'oid': 123
}


class TestTable(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = []
        colls = [
            '_columns', 'columns',
            '_rules', 'rules',
            '_triggers', 'triggers'
        ]
        utils.init_base(View, props, colls)

    def test_from_node_query(self):
        utils.from_node_query_base(View, NODE_ROW, self._validate_view)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            View,
            NODE_ROW,
            lambda conn: View.get_nodes_for_parent(conn, 0),
            self._validate_view
        )

    # METHOD TESTS #########################################################
    def test_refresh(self):
        # Setup: Create a table object and mock up the node collection reset method
        mock_conn = ServerConnection(utils.MockConnection(None))
        view = View._from_node_query(mock_conn, **NODE_ROW)
        view._columns.reset = mock.MagicMock()
        view._rules.reset = mock.MagicMock()
        view._triggers.reset = mock.MagicMock()

        # If: I refresh a table object
        view.refresh()

        # Then: The child object node collections should have been reset
        view._columns.reset.assert_called_once()
        view._rules.reset.assert_called_once()
        view._triggers.reset.assert_called_once()

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_view(self, view: View, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(view._conn, mock_conn)
        self.assertEqual(view._oid, NODE_ROW['oid'])
        self.assertEqual(view.oid, NODE_ROW['oid'])
        self.assertEqual(view._name, NODE_ROW['name'])
        self.assertEqual(view.name, NODE_ROW['name'])

        # Child objects
        self.assertIsInstance(view._columns, NodeCollection)
        self.assertIs(view.columns, view._columns)
        self.assertIsInstance(view._rules, NodeCollection)
        self.assertIs(view.rules, view._rules)
        self.assertIsInstance(view._triggers, NodeCollection)
        self.assertIs(view.triggers, view._triggers)
