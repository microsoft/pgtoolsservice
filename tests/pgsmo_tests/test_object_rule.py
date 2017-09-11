# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.table_objects.rule import Rule
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestRule(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'rulename',
        'oid': 123
    }

    @property
    def full_properties(self):
        return {
            "view": "view",
            "event": "event",
            "condition": "condition",
            "do_instead": "do_instead",
            "statements": "statements",
            "comment": "comment",
            "display_comments": "display_comments",
            "rid": "rid",
            "rulename": "rulename"
        }

    @property
    def property_query(self):
        return {
            "view": "test",
            "event": "test",
            "condition": "test",
            "do_instead": "test",
            "statements": "test",
            "comment": "test",
            "display_comments": "test",
            "rid": "test",
            "rulename": "test"
        }

    @property
    def class_for_test(self):
        return Rule

    @property
    def basic_properties(self):
        return {}

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestRule.NODE_ROW
