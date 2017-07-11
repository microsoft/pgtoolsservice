# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

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
        props = [
            '_tablespace', 'tablespace',
            '_allow_conn', 'allow_conn',
            '_can_create', 'can_create',
            '_owner_oid'
        ]
        colls = ['_schemas', 'schemas']     # When connected, these are actually defined
        name = 'dbname'
        mock_conn = ServerConnection(utils.MockConnection(None, name=name))
        db = Database(mock_conn, name)
        utils.validate_init(
            Database, name, mock_conn, db, props, colls,
            lambda obj: self._init_validation(obj, True)
        )

    def test_init_disconnected(self):
        props = [
            '_tablespace', 'tablespace',
            '_allow_conn', 'allow_conn',
            '_can_create', 'can_create',
            '_owner_oid',
            '_schemas', 'schemas'   # When not connected we want these to be set to None
        ]
        colls = []
        name = 'dbname'
        mock_conn = ServerConnection(utils.MockConnection(None, name='notconnected'))
        db = Database(mock_conn, name)
        utils.validate_init(
            Database, name, mock_conn, db, props, colls,
            lambda obj: self._init_validation(obj, False)
        )

    def test_from_node_query(self):
        utils.from_node_query_base(Database, DATABASE_ROW, self._validate_database)

    def test_get_nodes_for_parent(self):
        # Use the test helper for this method
        utils.get_nodes_for_parent_base(Database, DATABASE_ROW, Database.get_nodes_for_parent, self._validate_database)

    # IMPLEMENTATION DETAILS ###############################################
    def _init_validation(self, obj: Database, is_connected: bool):
        self.assertEqual(obj._is_connected, is_connected)

    def _validate_database(self, db: Database, mock_conn: ServerConnection):
        # NodeObject basic properties
        utils.validate_node_object_props(db, mock_conn, DATABASE_ROW['name'], DATABASE_ROW['did'])

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
