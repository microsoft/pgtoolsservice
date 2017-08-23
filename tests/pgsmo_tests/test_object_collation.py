# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo import Collation
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestCollation(NodeObjectTestBase, unittest.TestCase):
    NODE_QUERY = {
        'name': 'collation',
        'oid': 123
    }

    PROPERTY_QUERY = {
        'owner': 'postgres',
        'schema': 'test_schema',
        'description': 'test',
        'lc_collate': 'test',
        'lc_type': 'test',
        'locale': 'test',
        'copy_collation': 'postgres.UTF-8',
        'cascade': True
    }

    @property
    def basic_properties(self):
        return {}

    @property
    def full_properties(self):
        return {
            'owner': 'owner',
            'schema': 'schema',
            'description': 'description',
            'lc_collate': 'lc_collate',
            'lc_type': 'lc_type',
            'locale': 'locale',
            'copy_collation': 'copy_collation',
            'cascade': 'cascade'
        }

    @property
    def class_for_test(self):
        return Collation

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestCollation.NODE_QUERY

    @property
    def property_query(self) -> dict:
        return TestCollation.PROPERTY_QUERY
