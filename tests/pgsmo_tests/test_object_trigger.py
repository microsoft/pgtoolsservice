# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo import Trigger
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestTrigger(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'triggername',
        'oid': 123,
        'is_enable_trigger': True
    }

    @property
    def class_for_test(self):
        return Trigger

    @property
    def basic_properties(self):
        return {
            '_is_enabled': TestTrigger.NODE_ROW['is_enable_trigger'],
            'is_enabled': TestTrigger.NODE_ROW['is_enable_trigger']
        }

    @property
    def full_properties(self):
        return {
            "lanname": "lanname",
            "tfunction": "tfunction",
            "name": "name",
            "is_constraint_trigger": "is_constraint_trigger",
            "fires": "fires",
            "evnt_insert": "evnt_insert",
            "evnt_delete": "evnt_delete",
            "evnt_truncate": "evnt_truncate",
            "evnt_update": "evnt_update",
            "columns": "columns",
            "deferrable": "deferrable",
            "initdeferred": "initdeferred",
            "is_row_trigger": "is_row_trigger",
            "whenclause": "whenclause",
            "prosrc": "prosrc",
            "args": "args",
            "description": "description",
            "cascade": "cascade",
            "is_enable_trigger": "is_enable_trigger"
        }

    @property
    def property_query(self):
        return {
            "lanname": "test",
            "tfunction": "test",
            "name": "test",
            "is_constraint_trigger": True,
            "fires": "test",
            "evnt_insert": "test",
            "evnt_delete": "test",
            "evnt_truncate": "test",
            "evnt_update": "test",
            "columns": "test_columns",
            "deferrable": True,
            "initdeferred": True,
            "is_row_trigger": True,
            "whenclause": "test",
            "prosrc": "test",
            "args": 1,
            "description": "test_description",
            "cascade": True,
            "is_enable_trigger": True
        }

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestTrigger.NODE_ROW
