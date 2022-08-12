# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import tests.utils as utils
from mysqlsmo.objects.server.server import Server
from mysqlsmo.objects.column.column import Column
from tests.mysqlsmo_tests.node_test_base import NodeObjectTestBase


class TestColumn(NodeObjectTestBase, unittest.TestCase):
    NODE_QUERY = {
        'name': 'abc',
        'type': 'character',
        'ordinal': 1,
        'column_key': 'PRI',
        'is_nullable': 'YES',
        'column_default': None,
        'auto_increment': '',
        'is_updatable': 1,
        'extra': ''
    }

    @property
    def basic_properties(self):
        return {
            '_column_ordinal': self.node_query['ordinal'] - 1,
            'column_ordinal': self.node_query['ordinal'] - 1,
            '_is_key': self.node_query['column_key'] == 'PRI',
            'is_key': self.node_query['column_key'] == 'PRI',
            '_is_unique': self.node_query['column_key'] == 'UNI',
            'is_unique': self.node_query['column_key'] == 'UNI',
            '_is_nullable': self.node_query['is_nullable'] == 'YES',
            'not_null': self.node_query['is_nullable'] == 'YES',
            '_default_value': self.node_query['column_default'],
            'default_value': self.node_query['column_default'],
            '_is_read_only': not self.node_query['is_updatable'],
            'is_readonly': not self.node_query['is_updatable'],
            '_is_auto_increment': 'auto_increment' in self.node_query['extra'],
            'is_auto_increment': 'auto_increment' in self.node_query['extra']
        }

    @property
    def class_for_test(self):
        return Column

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
