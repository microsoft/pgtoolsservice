# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.server.server import Server
from pgsmo.objects.table_objects.column import Column
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase
import tests.pgsmo_tests.utils as utils


class TestColumn(NodeObjectTestBase, unittest.TestCase):
    NODE_QUERY = {
        'name': 'abc',
        'datatype': 'character',
        'oid': 123,
        'has_default_val': True,
        'not_null': True
    }

    @property
    def class_for_test(self):
        return Column

    @property
    def basic_properties(self):
        return {
            'has_default_value': self.node_query['has_default_val'],
            '_has_default_value': self.node_query['has_default_val'],
            'not_null': self.node_query['not_null'],
            '_not_null': self.node_query['not_null'],
        }

    @property
    def collections(self):
        return []

    @property
    def init_lambda(self):
        return lambda server, parent, name: Column(server, parent, name, 'character')

    @property
    def node_query(self):
        return TestColumn.NODE_QUERY

    # CUSTOM VALIDATION ####################################################
    @staticmethod
    def _custom_validate_from_node(obj, mock_server: Server):
        # Make sure that the datatype value is set
        utils.assert_threeway_equals('character', obj._datatype, obj.datatype)

    @staticmethod
    def _custom_validate_init(obj, mock_server: Server):
        # Make sure that the datatype value is set
        utils.assert_threeway_equals('character', obj._datatype, obj.datatype)
