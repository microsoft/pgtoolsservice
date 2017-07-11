# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects import Trigger
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'idxname',
    'oid': 123,
    'is_enable_trigger': True
}

class TestTrigger(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = ['_is_enabled', 'is_enabled']
        utils.init_base(Trigger, props, [])

    def test_from_node_query(self):
        utils.from_node_query_base(Trigger, NODE_ROW, self._validate)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Trigger,
            NODE_ROW,
            lambda conn: Trigger.get_nodes_for_parent(conn, 0),
            self._validate
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate(self, obj: Trigger, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, NODE_ROW['oid'])
        self.assertEqual(obj.oid, NODE_ROW['oid'])
        self.assertEqual(obj._name, NODE_ROW['name'])
        self.assertEqual(obj.name, NODE_ROW['name'])

        # Trigger-specific properties
        self.assertEqual(obj._is_enabled, NODE_ROW['is_enable_trigger'])
        self.assertEqual(obj.is_enabled, NODE_ROW['is_enable_trigger'])