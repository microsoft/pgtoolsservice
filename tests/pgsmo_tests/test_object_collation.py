# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.collation import Collation
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'collation',
    'oid': 123
}


class TestCollation(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        utils.init_base(Collation, [], [])

    def test_from_node_query(self):
        utils.from_node_query_base(Collation, NODE_ROW, self._validate)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Collation,
            NODE_ROW,
            lambda conn: Collation.get_nodes_for_parent(conn, 0),
            self._validate
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate(self, obj: Collation, mock_conn: ServerConnection):
        utils.validate_node_object_props(obj, mock_conn, NODE_ROW['name'], NODE_ROW['oid'])
