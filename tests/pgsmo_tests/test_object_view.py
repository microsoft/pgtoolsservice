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
        colls = ['_columns', 'columns']
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

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_view(self, view: View, mock_conn: ServerConnection):
        utils.validate_node_object_props(view, mock_conn, NODE_ROW['name'], NODE_ROW['oid'])

        # Child objects
        self.assertIsInstance(view._columns, NodeCollection)
        self.assertIs(view.columns, view._columns)
