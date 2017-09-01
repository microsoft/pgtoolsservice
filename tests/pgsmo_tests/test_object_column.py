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
        'not_null': True,
        'isprimarykey': True,
        'is_updatable': False,
        'isunique': True,
        'typoid': 1234,
        'default': 'nextval('
    }

    @property
    def basic_properties(self):
        return {
            'has_default_value': self.node_query['has_default_val'],
            '_has_default_value': self.node_query['has_default_val'],
            'not_null': self.node_query['not_null'],
            '_not_null': self.node_query['not_null'],
            '_column_ordinal': self.node_query['oid'] - 1,
            'column_ordinal': self.node_query['oid'] - 1,
            '_is_key': self.node_query['isprimarykey'],
            'is_key': self.node_query['isprimarykey'],
            '_is_readonly': self.node_query['is_updatable'] is False,
            'is_readonly': self.node_query['is_updatable'] is False,
            '_is_unique': self.node_query['isunique'],
            'is_unique': self.node_query['isunique'],
            '_type_oid': self.node_query['typoid'],
            'type_oid': self.node_query['typoid'],
            '_default_value': self.node_query['default'],
            'default_value': self.node_query['default'],
            '_is_auto_increament': True,
            'is_auto_increament': True,

        }

    @property
    def full_properties(self):
        return {
            "name": "name",
            "cltype": "cltype",
            "schema": "schema",
            "table": "table",
            "displaytypname": "displaytypname",
            "attlen": "attlen",
            "attprecision": "attprecision",
            "hasSqrBracket": "hasSqrBracket",
            "collspcname": "collspcname",
            "attnotnull": "attnotnull",
            "defval": "defval",
            "description": "description",
            "attoptions": "attoptions",
            "attacl": "attacl",
            "seclabels": "seclabels",
            "attstattarget": "attstattarget",
            "attstorage": "attstorage",
            "is_sql": "is_sql"
        }

    @property
    def property_query(self):
        return {
            "name": "test",
            "cltype": "test",
            "schema": "test_schema",
            "table": "test_table",
            "displaytypname": "test_displaytypname",
            "attlen": "test",
            "attprecision": "test",
            "hasSqrBracket": "test",
            "collspcname": "test",
            "attnotnull": "test",
            "defval": "test",
            "description": "test_description",
            "attoptions": "test",
            "attacl": "test",
            "seclabels": "test",
            "attstattarget": "test",
            "attstorage": "test",
            "is_sql": "test"
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
