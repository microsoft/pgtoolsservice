# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.schema.schema import Schema
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


SCHEMA_ROW = {
    'name': 'schema',
    'oid': 123,
    'can_create': True,
    'has_usage': True
}


class TestSchema(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        props = ['_can_create', 'can_create', '_has_usage', 'has_usage']
        collections = [
            '_collations', 'collations',
            '_functions', 'functions',
            '_sequences', 'sequences',
            '_tables', 'tables',
            '_views', 'views'
        ]
        utils.init_base(Schema, props, collections)

    def test_from_node_query(self):
        utils.from_node_query_base(Schema, SCHEMA_ROW, self._validate_schema)

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_schema(self, schema: Schema, mock_conn: ServerConnection):
        utils.validate_node_object_props(schema, mock_conn, SCHEMA_ROW['name'], SCHEMA_ROW['oid'])

        # Schema-specific basic properties
        self.assertEqual(schema._can_create, SCHEMA_ROW['can_create'])
        self.assertEqual(schema.can_create, SCHEMA_ROW['can_create'])
        self.assertEqual(schema._has_usage, SCHEMA_ROW['has_usage'])
        self.assertEqual(schema.has_usage, SCHEMA_ROW['has_usage'])

        # Child objects
        self.assertIsInstance(schema._collations, NodeCollection)
        self.assertIs(schema.collations, schema._collations)
        self.assertIsInstance(schema._functions, NodeCollection)
        self.assertIs(schema.functions, schema._functions)
        self.assertIsInstance(schema._sequences, NodeCollection)
        self.assertIs(schema.sequences, schema._sequences)
        self.assertIsInstance(schema._tables, NodeCollection)
        self.assertIs(schema.tables, schema._tables)
        self.assertIsInstance(schema._views, NodeCollection)
        self.assertIs(schema.views, schema._views)
