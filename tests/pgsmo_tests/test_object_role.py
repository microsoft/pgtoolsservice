# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.role.role import Role
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


ROLE_ROW = {
    'rolname': 'role',
    'oid': 123,
    'rolcanlogin': True,
    'rolsuper': True
}


class TestRole(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = ['_can_login', 'can_login', '_super', 'super']
        colls = []
        utils.init_base(Role, props, colls)

    def test_from_node_query(self):
        utils.from_node_query_base(Role, ROLE_ROW, self._validate_role)

    def test_get_nodes_for_parent(self):
        # Use the test helper
        utils.get_nodes_for_parent_base(Role, ROLE_ROW, Role.get_nodes_for_parent, self._validate_role)

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_role(self, role: Role, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(role._conn, mock_conn)
        self.assertEqual(role._oid, ROLE_ROW['oid'])
        self.assertEqual(role.oid, ROLE_ROW['oid'])
        self.assertEqual(role._name, ROLE_ROW['rolname'])
        self.assertEqual(role.name, ROLE_ROW['rolname'])

        # Role-specific basic properties
        self.assertEqual(role._can_login, ROLE_ROW['rolcanlogin'])
        self.assertEqual(role.can_login, ROLE_ROW['rolcanlogin'])
        self.assertEqual(role._super, ROLE_ROW['rolsuper'])
        self.assertEqual(role.super, ROLE_ROW['rolsuper'])
