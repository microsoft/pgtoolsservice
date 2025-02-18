# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo import Extension
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestExtension(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        "name": "ex",
        "oid": 123,
        "schema": "public",
        "schemaoid": 456,
        "objectname": "extension",
        "is_system": True,
    }

    @property
    def class_for_test(self):
        return Extension

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestExtension.NODE_ROW

    @property
    def full_properties(self):
        return {"owner": "owner", "relocatable": "relocatable", "version": "version"}

    @property
    def property_query(self) -> dict:
        return {"owner": "postgres", "relocatable": False, "version": "1.0"}
