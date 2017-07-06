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
    def test_init(self):
        # If: I create a new role object
        mock_conn = ServerConnection(utils.MockConnection(None))
        mock_name = 'role1'
        role = Role(mock_conn, mock_name)

        # Then:
        # ... The role should be an instance of a node object
        self.assertIsInstance(role, NodeObject)
        self.assertIsInstance(role, Role)

        # ... The node object properties should be assigned properly
        self.assertIs(role._conn, mock_conn)
        self.assertIsNone(role._oid)
        self.assertIsNone(role.oid)
        self.assertEqual(role._name, mock_name)
        self.assertEqual(role.name, mock_name)

        # ... The role-specific basic properties should be set to none
        self.assertIsNone(role._can_login)
        self.assertIsNone(role.can_login)
        self.assertIsNone(role._super)
        self.assertIsNone(role.super)

    def test_from_node_query(self):
        # If: I crate a new role object from a node query row
        mock_conn = ServerConnection(utils.MockConnection(None))
        role = Role._from_node_query(mock_conn, **ROLE_ROW)

        # Then:
        # ... The role should be an instance of a Role
        self.assertIsInstance(role, NodeObject)
        self.assertIsInstance(role, Role)

        # ... The properties should be assigned properly based on the row
        self._validate_role(role, mock_conn)

    def test_get_nodes_for_parent(self):
        # Use the test helper
        utils.get_nodes_for_parent_base(Role, ROLE_ROW, Role.get_nodes_for_parent, self._validate_role)

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
