# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table.table import Table
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestTable(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'tablename',
        'oid': 123
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
        return {}