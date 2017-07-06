# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeObject, NodeCollection
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
        collections = ['_tables', 'tables', '_views', 'views']
        utils.init_base(Schema, props, collections)

    def test_from_node_query(self):
        # If: I create a new schema object from a node row
        mock_conn = ServerConnection(utils.MockConnection(None))
        schema = Schema._from_node_query(mock_conn, **SCHEMA_ROW)

        # Then:
        # ... The returned object must be a schema
        self.assertIsInstance(schema, NodeObject)
        self.assertIsInstance(schema, Schema)

        self._validate_schema(schema, mock_conn)

    def test_from_nodes_for_parent(self):
        # Use the test helper for this method
        utils.get_nodes_for_parent_base(Schema, SCHEMA_ROW, Schema.get_nodes_for_parent, self._validate_schema)

    # METHOD TESTS #########################################################
    def test_refresh(self):
        # Setup: Create a schema object and mock up the node collection reset methods
        mock_conn = ServerConnection(utils.MockConnection(None))
        schema = Schema._from_node_query(mock_conn, **SCHEMA_ROW)
        schema._tables.reset = mock.MagicMock()
        schema._views.reset = mock.MagicMock()

        # If: I refresh a schema object
        schema.refresh()

        # Then: The child object node collections should have been reset
        schema._tables.reset.assert_called_once()
        schema._views.reset.assert_called_once()

    def _validate_schema(self, schema: Schema, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(schema._conn, mock_conn)
        self.assertEqual(schema._oid, SCHEMA_ROW['oid'])
        self.assertEqual(schema.oid, SCHEMA_ROW['oid'])
        self.assertEqual(schema._name, SCHEMA_ROW['name'])
        self.assertEqual(schema.name, SCHEMA_ROW['name'])

        # Schema-specific basic properties
        self.assertEqual(schema._can_create, SCHEMA_ROW['can_create'])
        self.assertEqual(schema.can_create, SCHEMA_ROW['can_create'])
        self.assertEqual(schema._has_usage, SCHEMA_ROW['has_usage'])
        self.assertEqual(schema.has_usage, SCHEMA_ROW['has_usage'])

        # Child objects
        self.assertIsInstance(schema._tables, NodeCollection)
        self.assertIs(schema.tables, schema._tables)
        self.assertIsInstance(schema._views, NodeCollection)
        self.assertIs(schema.views, schema._views)
