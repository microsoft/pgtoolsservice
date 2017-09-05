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
        'oid': 123
    }

    @property
    def basic_properties(self):
        return {}

    @property
    def full_properties(self):
        return {
            "name": "name",
            "schema": "schema",
            "table": "table",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "indconstraint": "indconstraint",
            "mode": "mode",
            "index": "index",
            "nspname": "nspname",
            "cascade": "cascade",
            "description": "description",
            "indisclustered": "indisclustered",
            "indisprimary": "indisprimary",
            "indisunique": "indisunique",
            "isconcurrent": "isconcurrent"
        }

    @property
    def property_query(self) -> dict:
        return {
            "name": "test",
            "schema": "test_schema",
            "table": "test_table",
            "amname": "amname",
            "columns": "columns",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "indconstraint": "indconstraint",
            "mode": "mode",
            "index": "index",
            "nspname": "nspname",
            "cascade": "cascade",
            "description": "description",
            "indisclustered": "indisclustered",
            "indisprimary": "indisprimary",
            "indisunique": "indisunique",
            "isconcurrent": "isconcurrent"
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

    @property
    def property_query(self) -> dict:
        return self.full_properties
