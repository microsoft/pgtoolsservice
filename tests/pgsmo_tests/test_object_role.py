# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

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

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_role(self, role: Role, mock_conn: ServerConnection):
        utils.validate_node_object_props(role, mock_conn, ROLE_ROW['rolname'], ROLE_ROW['oid'])

        # Role-specific basic properties
        self.assertEqual(role._can_login, ROLE_ROW['rolcanlogin'])
        self.assertEqual(role.can_login, ROLE_ROW['rolcanlogin'])
        self.assertEqual(role._super, ROLE_ROW['rolsuper'])
        self.assertEqual(role.super, ROLE_ROW['rolsuper'])
