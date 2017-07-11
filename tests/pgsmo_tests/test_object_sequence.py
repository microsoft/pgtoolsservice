# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.sequence import Sequence
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'name',
    'oid': 123
}


class TestSequence(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        utils.init_base(Sequence, [], [])

    def test_from_node_query(self):
        utils.from_node_query_base(Sequence, NODE_ROW, self._validate)

    def test_from_nodes_for_parent(self):
        utils.get_nodes_for_parent_base(
            Sequence,
            NODE_ROW,
            lambda conn: Sequence.get_nodes_for_parent(conn, 0),
            self._validate
        )

    # IMPLEMENTATION DETAILS ###############################################
    def _validate(self, obj: Sequence, mock_conn: ServerConnection):
        utils.validate_node_object_props(obj, mock_conn, NODE_ROW['name'], NODE_ROW['oid'])
