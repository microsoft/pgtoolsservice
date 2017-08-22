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

    @property
    def class_for_test(self):
        return Collation

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestCollation.NODE_QUERY
