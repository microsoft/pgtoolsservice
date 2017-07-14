# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.functions.function import Function
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase


class TestFunction(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'funcname(arg1 int)',
        'oid': 123,
        'description': 'func description',
        'lanname': 'sql',
        'funcowner': 'postgres'
    }

    @property
    def class_for_test(self):
        return Function

    @property
    def basic_properties(self):
        return {
            'description': TestFunction.NODE_ROW['description'],
            '_description': TestFunction.NODE_ROW['description'],
            'language': TestFunction.NODE_ROW['lanname'],
            '_lanname': TestFunction.NODE_ROW['lanname'],
            'owner': TestFunction.NODE_ROW['funcowner'],
            '_owner': TestFunction.NODE_ROW['funcowner']
        }

    @property
    def collections(self):
        return []

    @property
    def node_query(self) -> dict:
        return TestFunction.NODE_ROW
