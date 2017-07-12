# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.functions import Function, FunctionBase, TriggerFunction
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

NODE_ROW = {
    'name': 'funcname(arg1 int)',
    'oid': 123,
    'description': 'func description',
    'lanname': 'sql',
    'funcowner': 'postgres'
}


class TestFunctions(unittest.TestCase):
    """These tests are for all function classes"""

    CONSTRAINT_CLASSES = [Function, TriggerFunction]

    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        for class_ in TestFunctions.CONSTRAINT_CLASSES:
            props = [
                '_description', 'description',
                'language_name', '_lanname',
                'owner', '_owner'
            ]
            utils.init_base(class_, props, [])

    def test_from_node_query(self):
        for class_ in TestFunctions.CONSTRAINT_CLASSES:
            utils.from_node_query_base(class_, NODE_ROW, self._validate)

    def test_get_nodes_for_parent(self):
        for class_ in TestFunctions.CONSTRAINT_CLASSES:
            get_nodes_for_parent = (lambda conn: class_.get_nodes_for_parent(conn, 10))
            utils.get_nodes_for_parent_base(class_, NODE_ROW, get_nodes_for_parent, self._validate)

    # IMPLEMENTATION DETAILS
    def _validate(self, obj: FunctionBase, mock_conn: ServerConnection):
        utils.validate_node_object_props(obj, mock_conn, NODE_ROW['name'], NODE_ROW['oid'])

        # Constraint specific basic properties
        utils.assert_threeway_equals(NODE_ROW['description'], obj.description, obj._description)
        utils.assert_threeway_equals(NODE_ROW['lanname'], obj.language_name, obj._lanname)
        utils.assert_threeway_equals(NODE_ROW['funcowner'], obj.owner, obj.owner)
