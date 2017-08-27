# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.role.role import Role
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestRole(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'role',
        'oid': 123,
        'rolcanlogin': True,
        'rolsuper': True
    }

    @property
    def class_for_test(self):
        return Role

    @property
    def basic_properties(self):
        return {
            '_can_login': TestRole.NODE_ROW['rolcanlogin'],
            'can_login': TestRole.NODE_ROW['rolcanlogin'],
            'is_super': TestRole.NODE_ROW['rolsuper'],
            '_is_super': TestRole.NODE_ROW['rolsuper']
        }

    @property
    def collections(self):
        return []

    @property
    def init_lambda(self):
        return lambda server, parent, name: Role(server, name)

    @property
    def node_query(self) -> dict:
        return TestRole.NODE_ROW

    @property
    def parent_expected_to_be_none(self) -> bool:
        return True
