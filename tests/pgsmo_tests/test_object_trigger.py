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
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestTrigger.NODE_ROW
