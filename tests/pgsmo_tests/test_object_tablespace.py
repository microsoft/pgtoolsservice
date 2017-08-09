# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.tablespace.tablespace import Tablespace
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestTablespace(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'test',
        'oid': 123,
        'owner': 10
    }

    @property
    def class_for_test(self):
        return Tablespace

    @property
    def basic_properties(self):
        return {
            'owner': TestTablespace.NODE_ROW['owner'],
            '_owner': TestTablespace.NODE_ROW['owner']
        }

    @property
    def collections(self):
        return []

    @property
    def init_lambda(self):
        return lambda server, parent, name: Tablespace(server, name)

    @property
    def node_query(self) -> dict:
        return TestTablespace.NODE_ROW

    @property
    def parent_expected_to_be_none(self) -> bool:
        return True

    @property
    def full_properties(self):
        return {
            "user": "user",
            "location": "location",
            "description": "description",
            "options": "options",
            "acl": "acl"
        }

    @property
    def property_query(self):
        return {
            "user": "test",
            "location": "some path",
            "description": None,
            "options": None,
            "acl": None
        }
