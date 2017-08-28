# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo import Collation
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestDatatype(NodeObjectTestBase, unittest.TestCase):
    NODE_QUERY = {
        'name': 'datatype',
        'oid': 123
    }

    @property
    def basic_properties(self):
        return {}

    @property
    def full_properties(self):
        # TODO: Add property query implementation, tracked by https://github.com/Microsoft/carbon/issues/1734
        return {}

    @property
    def class_for_test(self):
        return Collation

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestDatatype.NODE_QUERY

    @property
    def property_query(self) -> dict:
        # TODO: Add property query implementation, tracked by https://github.com/Microsoft/carbon/issues/1734
        return {}
