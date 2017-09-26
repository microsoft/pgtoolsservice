# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects.index import Index
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestIndex(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'idxname',
        'oid': 123,
        'indisclustered': True,
        'indisprimary': True,
        'indisunique': True
    }

    @property
    def basic_properties(self):
        return {}

    @property
    def full_properties(self):
        return {
            "name": "name",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "indconstraint": "indconstraint",
            "mode": "mode",
            "index": "index",
            "cascade": "cascade",
            "description": "description",
            "is_clustered": "is_clustered",
            "is_valid": "is_valid",
            "is_unique": "is_unique",
            "is_primary": "is_primary",
            "is_concurrent": "is_concurrent"
        }

    @property
    def property_query(self) -> dict:
        return {
            "name": "test",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": None,
            "spcname": "spcname",
            "indconstraint": "indconstraint",
            "mode": "test_mode",
            "index": "index",
            "cascade": True,
            "description": None,
            "is_clustered": True,
            "is_valid": True,
            "is_unique": True,
            "is_primary": True,
            "is_concurrent": True
        }

    @property
    def class_for_test(self):
        return Index

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestIndex.NODE_ROW
