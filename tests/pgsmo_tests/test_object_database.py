# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock    # noqa

from pgsmo.objects.database.database import Database
from pgsmo.objects.server.server import Server
from smo.common.node_object import NodeCollection
from tests.pgsmo_tests.node_test_base import NodeObjectTestBase
from tests.pgsmo_tests.utils import MockPGServerConnection


class TestDatabase(NodeObjectTestBase, unittest.TestCase):
    NODE_ROW = {
        'name': 'dbname',
        'oid': 123,
        'spcname': 'primary',
        'datallowconn': True,
        'cancreate': True,
        'owner': 10,
        'datistemplate': False,
        'canconnect': True,
        'is_system': False,
        'datlastsysoid': 12368
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

    @property
    def _full_properties(self):
        return {
            "encoding": "encoding",
            "template": "template",
            "datcollate": "datcollate",
            "datctype": "datctype",
            "spcname": "spcname",
            "datconnlimit": "datconnlimit"
        }

    @property
    def property_query(self):
        return {
            "encoding": "UTF8",
            "template": None,
            "datcollate": False,
            "datctype": None,
            "spcname": "test",
            "datconnlimit": 0
        }

    # CONSTRUCTION TESTS ###################################################
    def test_init(self):
        """Overriding to prevent using default init testing"""
        pass

    def test_init_connected(self):
        # If: I create a DB that is connected
        name = 'dbname'
        mock_server = Server(MockPGServerConnection(None, name=name))
        db = Database(mock_server, name)

        # Then:
        # ... Default validation should pass
        self._init_validation(db, mock_server, None, name)

        # ... The schema node collection should be defined
        self.assertIsInstance(db._schemas, NodeCollection)
        self.assertIs(db.schemas, db._schemas)

    def test_init_not_connected(self):
        # If: I create a DB that is connected
        name = 'dbname'
        mock_conn = Server(MockPGServerConnection(None, name='not_connected'))
        db = Database(mock_conn, name)

        # Then:
        # ... Default validation should pass
        self._init_validation(db, mock_conn, None, name)

        # ... The schema node collection should not be defined
        self.assertIsNotNone(db._schemas)
        self.assertIsNotNone(db.schemas)
