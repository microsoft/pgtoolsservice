# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.view.materialized_view import MaterializedView
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestMaterializedView(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'viewname',
        'oid': 123,
        'schema': 'public',
        'schemaoid': 456,
        'objectname': 'viewname',
        'is_system': True
    }

    @property
    def class_for_test(self):
        return MaterializedView

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return [
            '_columns', 'columns',
            '_indexes', 'indexes'
        ]

    @property
    def node_query(self) -> dict:
        return TestMaterializedView.NODE_ROW

    @property
    def full_properties(self):
        return {
            "definition": "definition",
            "owner": "owner",
            "comment": "comment",
            "nspname": "nspname",
            "check_option": "check_option",
            "security_barrier": "security_barrier"
        }

    @property
    def property_query(self) -> dict:
        return {
            "schema": "public",
            "definition": None,
            "owner": "admin",
            "comment": "this is a comment",
            "nspname": "test",
            "check_option": False,
            "security_barrier": None
        }
