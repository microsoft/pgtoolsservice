# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.schema.schema import Schema
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestSchema(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'schema',
        'oid': 123,
        'can_create': True,
        'has_usage': True
    }

    @property
    def class_for_test(self):
        return Schema

    @property
    def basic_properties(self):
        return {
            'can_create': TestSchema.NODE_ROW['can_create'],
            '_can_create': TestSchema.NODE_ROW['can_create'],
            'has_usage': TestSchema.NODE_ROW['has_usage'],
            '_has_usage': TestSchema.NODE_ROW['has_usage']
        }

    @property
    def collections(self):
        return [
            '_collations', 'collations',
            '_functions', 'functions',
            '_sequences', 'sequences',
            '_tables', 'tables',
            '_trigger_functions', 'trigger_functions',
            '_views', 'views'
        ]

    @property
    def node_query(self):
        return TestSchema.NODE_ROW

    @property
    def _full_properties(self):
        return {
            "namespaceowner": "namespaceowner",
            "description": "description",
            "nspacl": "nspacl",
            "seclabels": "seclabels",
            "cascade": "cascade"
        }

    @property
    def property_query(self):
        return {
            "namespaceowner": "admin",
            "description": "test",
            "nspacl": None,
            "seclabels": None,
            "cascade": False
        }
