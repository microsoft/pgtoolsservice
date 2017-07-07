# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.functions.function import Function
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'funcname(arg1 int)',
    'oid': 123,
    'description': 'func description',
    'lanname': 'sql',
    'funcowner': 'postgres'
}


class TestFunction(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = [
            '_description', 'description',
            '_lanname', 'language',
            '_owner', 'owner'
        ]
        colls = []
        utils.init_base(Function, props, colls)

    def test_from_node_query(self):
        utils.from_node_query_base(Function, NODE_ROW, self._validate)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Function,
            NODE_ROW,
            lambda conn: Function.get_nodes_for_parent(conn, 0),
            self._validate
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate(self, obj: Function, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, NODE_ROW['oid'])
        self.assertEqual(obj.oid, NODE_ROW['oid'])
        self.assertEqual(obj._name, NODE_ROW['name'])
        self.assertEqual(obj.name, NODE_ROW['name'])

        # Function basic properties
        self.assertEqual(obj._description, NODE_ROW['description'])
        self.assertEqual(obj.description, NODE_ROW['description'])
        self.assertEqual(obj._lanname, NODE_ROW['lanname'])
        self.assertEqual(obj.language, NODE_ROW['lanname'])
        self.assertEqual(obj._owner, NODE_ROW['funcowner'])
        self.assertEqual(obj.owner, NODE_ROW['funcowner'])
