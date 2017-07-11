# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects.rule import Rule
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'rulename',
    'oid': 123
}


class TestIndex(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = []
        colls = []
        utils.init_base(Rule, props, colls)

    def test_from_node_query(self):
        utils.from_node_query_base(Rule, NODE_ROW, self._validate)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Rule,
            NODE_ROW,
            lambda conn: Rule.get_nodes_for_parent(conn, 0),
            self._validate
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate(self, obj: Rule, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, NODE_ROW['oid'])
        self.assertEqual(obj.oid, NODE_ROW['oid'])
        self.assertEqual(obj._name, NODE_ROW['name'])
        self.assertEqual(obj.name, NODE_ROW['name'])
