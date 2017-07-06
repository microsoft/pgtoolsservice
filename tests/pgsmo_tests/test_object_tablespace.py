# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.tablespace.tablespace import Tablespace
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'test',
    'oid': 123,
    'owner': 10
}


class TestTablespace(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = ['owner', '_owner']
        utils.init_base(Tablespace, props, [])
    
    def test_from_node_query(self):
        utils.from_node_query_base(Tablespace, NODE_ROW, self._validate_tablespace)

    def test_get_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Tablespace,
            NODE_ROW,
            Tablespace.get_nodes_for_parent,
            self._validate_tablespace
        )
        
    # IMPLEMENTATION DETAILS ###############################################
    def _validate_tablespace(self, obj: Tablespace, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, NODE_ROW['oid'])
        self.assertEqual(obj.oid, NODE_ROW['oid'])
        self.assertEqual(obj._name, NODE_ROW['name'])
        self.assertEqual(obj.name, NODE_ROW['name'])

        # Tablespace-specific properties
        self.assertEqual(obj._owner, NODE_ROW['owner'])
        self.assertEqual(obj.owner, NODE_ROW['owner'])

