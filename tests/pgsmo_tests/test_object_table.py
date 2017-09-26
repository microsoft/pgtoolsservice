# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table.table import Table
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestTable(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'public.tablename',
        'oid': 123,
        'schema': 'public',
        'schemaoid': 456,
        'objectname': 'tablename'
    }

    @property
    def class_for_test(self):
        return Table

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return [
            '_check_constraints', 'check_constraints',
            '_columns', 'columns',
            '_exclusion_constraints', 'exclusion_constraints',
            '_foreign_key_constraints', 'foreign_key_constraints',
            '_index_constraints', 'index_constraints',
            '_indexes', 'indexes',
            '_rules', 'rules',
            '_triggers', 'triggers'
        ]

    @property
    def node_query(self) -> dict:
        return TestTable.NODE_ROW

    @property
    def full_properties(self):
        return {
            "coll_inherits": "coll_inherits",
            "typname": "typname",
            "like_relation": "like_relation",
            "primary_key": "primary_key",
            "unique_constraint": "unique_constraint",
            "foreign_key": "foreign_key",
            "check_constraint": "check_constraint",
            "exclude_constraint": "exclude_constraint",
            "fillfactor": "fillfactor",
            "spcname": "spcname",
            "owner": "owner",
            "cascade": "cascade",
            "coll_inherits_added": "coll_inherits_added",
            "coll_inherits_removed": "coll_inherits_removed",
            "autovacuum_custom": "autovacuum_custom",
            "autovacuum_enabled": "autovacuum_enabled",
            "vacuum_table": "vacuum_table",
            "toast_autovacuum": "toast_autovacuum",
            "toast_autovacuum_enabled": "toast_autovacuum_enabled",
            "vacuum_toast": "vacuum_toast",
            "description": "description",
            "acl": "acl",
            "seclabels": "seclabels",
            "hasoids": "hasoids"
        }

    @property
    def property_query(self) -> dict:
        return {
            "coll_inherits": 0,
            "typname": "test",
            "like_relation": None,
            "primary_key": 42,
            "unique_constraint": None,
            "foreign_key": 123,
            "check_constraint": None,
            "exclude_constraint": False,
            "fillfactor": None,
            "spcname": "test",
            "owner": "admin",
            "cascade": False,
            "coll_inherits_added": 0,
            "coll_inherits_removed": 0,
            "autovacuum_custom": None,
            "autovacuum_enabled": True,
            "vacuum_table": False,
            "toast_autovacuum": None,
            "toast_autovacuum_enabled": False,
            "vacuum_toast": False,
            "description": "generic description",
            "acl": None,
            "seclabels": None,
            "hasoids": False
        }
