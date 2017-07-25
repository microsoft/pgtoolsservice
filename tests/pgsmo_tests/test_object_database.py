# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.database.database import Database
from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.server.server import Server
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase
import tests.pgsmo_tests.utils as utils


class TestDatabase(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'dbname',
        'oid': 123,
        'spcname': 'primary',
        'datallowconn': True,
        'cancreate': True,
        'owner': 10
    }

    @property
    def class_for_test(self):
        return Database

    @property
    def basic_properties(self):
        return {
            'tablespace': TestDatabase.NODE_ROW['spcname'],
            '_tablespace': TestDatabase.NODE_ROW['spcname'],
            'allow_conn': TestDatabase.NODE_ROW['datallowconn'],
            '_allow_conn': TestDatabase.NODE_ROW['datallowconn'],
            'can_create': TestDatabase.NODE_ROW['cancreate'],
            '_can_create': TestDatabase.NODE_ROW['cancreate'],
            '_owner_oid': TestDatabase.NODE_ROW['owner']
        }

    @property
    def collections(self):
        """
        Although a db has collections under it, we return none here b/c we will be performing
        custom validation of the collections based on whether or not the DB is connected
        """
        return []

    @property
    def init_lambda(self):
        return lambda server, parent, name: Database(server, name)

    @property
    def node_query(self) -> dict:
        return TestDatabase.NODE_ROW

    @property
    def parent_expected_to_be_none(self) -> bool:
        return True

    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        """Overriding to prevent using default init testing"""
        pass

    def test_init_connected(self):
        # If: I create a DB that is connected
        name = 'dbname'
        mock_server = Server(utils.MockConnection(None, name=name))
        db = Database(mock_server, name)

        # Then:
        # ... Default validation should pass
        self._init_validation(db, mock_server, None, name)

        # ... The database should be connected
        self.assertTrue(db._is_connected)

        # ... The schema node collection should be defined
        self.assertIsInstance(db._schemas, NodeCollection)
        self.assertIs(db.schemas, db._schemas)

    def test_init_not_connected(self):
        # If: I create a DB that is connected
        name = 'dbname'
        mock_conn = Server(utils.MockConnection(None, name='not_connected'))
        db = Database(mock_conn, name)

        # Then:
        # ... Default validation should pass
        self._init_validation(db, mock_conn, None, name)

        # ... The database should be connected
        self.assertFalse(db._is_connected)

        # ... The schema node collection should not be defined
        self.assertIsNone(db._schemas)
        self.assertIsNone(db.schemas)
