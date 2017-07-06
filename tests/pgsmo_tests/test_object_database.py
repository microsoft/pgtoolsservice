# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeObject, NodeCollection
from pgsmo.objects.database.database import Database
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils

DATABASE_ROW = {
    'name': 'dbname',
    'did': 123,
    'spcname': 'primary',
    'datallowconn': True,
    'cancreate': True,
    'owner': 10
}


class TestDatabase(unittest.TestCase):
    # CONSTRUCTION TESTS ###################################################
    def test_init_connected(self):
        # If: I create a new database object that is connected
        mock_conn = ServerConnection(utils.MockConnection(None, name=DATABASE_ROW['name']))
        mock_name = DATABASE_ROW['name']
        db = Database(mock_conn, mock_name)

        # Then:
        # ... The column should be an instance of a node object
        self.assertIsInstance(db, NodeObject)

        # ... The properties should be set properly
        self._validate_database_init(db, mock_conn, True)

    def test_init_disconnected(self):
        # If: I create a new database object that is not connected
        mock_conn = ServerConnection(utils.MockConnection(None))
        mock_name = DATABASE_ROW['name']
        db = Database(mock_conn, mock_name)

        # Then:
        # ... The column should be an instance of a node object
        self.assertIsInstance(db, NodeObject)

        # ... The properties should be set properly
        self._validate_database_init(db, mock_conn, False)

    def test_from_node_query(self):
        # If: I create a column from a node query
        mock_conn = ServerConnection(utils.MockConnection(None))
        db = Database._from_node_query(mock_conn, **DATABASE_ROW)

        # Then:
        # ... The returned obj must be a database
        self.assertIsInstance(db, NodeObject)
        self.assertIsInstance(db, Database)

        self._validate_database(db, mock_conn)

    def test_get_nodes_for_parent(self):
        # Use the test helper for this method
        utils.get_nodes_for_parent_base(Database, DATABASE_ROW, Database.get_nodes_for_parent, self._validate_database)

    # METHOD TESTS #########################################################
    def test_refresh(self):
        # Setup: Create a database object and overwrite the reset method of the child objects
        db = Database(ServerConnection(utils.MockConnection(None, name=DATABASE_ROW['name'])), DATABASE_ROW['name'])
        db._schemas.reset = mock.MagicMock()

        # If: I refresh the database
        db.refresh()

        # Then: The mocks should have been called
        db._schemas.reset.assert_called_once()

    # IMPLEMENTATION DETAILS ###############################################
    def _validate_database_init(self, db: Database, mock_conn: ServerConnection, is_connected=False):
        # ... All the properties should be assigned properly
        self.assertIs(db._conn, mock_conn)
        self.assertEqual(db._is_connected, is_connected)

        self.assertIsNone(db._oid, None)
        self.assertIsNone(db.oid, None)
        self.assertEqual(db._name, DATABASE_ROW['name'])
        self.assertEqual(db.name, DATABASE_ROW['name'])

        self.assertIsNone(db._tablespace)
        self.assertIsNone(db.tablespace)
        self.assertIsNone(db._allow_conn)
        self.assertIsNone(db.allow_conn)
        self.assertIsNone(db._can_create)
        self.assertIsNone(db.can_create)
        self.assertIsNone(db._owner_oid)

        if is_connected:
            self.assertTrue(db._is_connected)
            self.assertIsInstance(db._schemas, NodeCollection)
            self.assertIs(db.schemas, db._schemas)
        else:
            self.assertFalse(db._is_connected)
            self.assertIsNone(db._schemas)
            self.assertIsNone(db.schemas)

    def _validate_database(self, db: Database, mock_conn: ServerConnection):
        # NodeObject basic properties
        self.assertIs(db._conn, mock_conn)
        self.assertEqual(db._oid, DATABASE_ROW['did'])
        self.assertEqual(db.oid, DATABASE_ROW['did'])
        self.assertEqual(db._name, DATABASE_ROW['name'])
        self.assertEqual(db.name, DATABASE_ROW['name'])

        # Database-specific basic properties
        self.assertEqual(db._tablespace, DATABASE_ROW['spcname'])
        self.assertEqual(db.tablespace, DATABASE_ROW['spcname'])
        self.assertEqual(db._allow_conn, DATABASE_ROW['datallowconn'])
        self.assertEqual(db.allow_conn, DATABASE_ROW['datallowconn'])
        self.assertEqual(db._can_create, DATABASE_ROW['cancreate'])
        self.assertEqual(db.can_create, DATABASE_ROW['cancreate'])
        self.assertEqual(db._owner_oid, DATABASE_ROW['owner'])

        # Child objects
        self.assertFalse(db._is_connected)
        self.assertIsNone(db._schemas)
        self.assertIsNone(db.schemas)
