# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects.constraints import Constraint, CheckConstraint, ExclusionConstraint, IndexConstraint
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'convalidated': True,
    'name': 'constraint',
    'oid': 123
}


class TestConstraints(unittest.TestCase):
    """These tests are for all constraint classes"""

    CONSTRAINT_CLASSES = [CheckConstraint, ExclusionConstraint, IndexConstraint]

    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        for class_ in TestConstraints.CONSTRAINT_CLASSES:
            props = [
                '_convalidated', 'convalidated',
            ]
            utils.init_base(class_, props, [])
            
    def test_from_node_query(self):
        for class_ in TestConstraints.CONSTRAINT_CLASSES:
            utils.from_node_query_base(class_, NODE_ROW, self._validate)
            
    def test_get_nodes_for_parent(self):
        for class_ in TestConstraints.CONSTRAINT_CLASSES:
            get_nodes_for_parent = (lambda conn: class_.get_nodes_for_parent(conn, 10))
            utils.get_nodes_for_parent_base(class_, NODE_ROW, get_nodes_for_parent, self._validate)

    # IMPLEMENTATION DETAILS 
    def _validate(self, obj: Constraint, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(obj._conn, mock_conn)
        self.assertEqual(obj._oid, NODE_ROW['oid'])
        self.assertEqual(obj.oid, NODE_ROW['oid'])
        self.assertEqual(obj._name, NODE_ROW['name'])
        self.assertEqual(obj.name, NODE_ROW['name'])

        # Constraint specific basic properties
        self.assertEqual(obj._convalidated, NODE_ROW['convalidated'])
        self.assertEqual(obj.convalidated, NODE_ROW['convalidated'])