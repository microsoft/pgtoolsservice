# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import unittest
import unittest.mock as mock
import urllib.parse as parse

import inflection

from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection
from pgsmo.objects.database.database import Database
from pgsmo.objects.server.server import Server
from smo.common.node_object import NodeCollection, NodeLazyPropertyCollection
from tests.pgsmo_tests.utils import MockPGServerConnection
from tests.utils import MockPsycopgConnection


class TestServer(unittest.TestCase):
    CHECK_RECOVERY_ROW = {
        'inrecovery': True,
        'isreplaypaused': True
    }

    def test_init(self):
        # If: I construct a new server object
        host = 'host'
        port = '1234'
        dbname = 'dbname'
        mock_conn = MockPGServerConnection(None, name=dbname, host=host, port=port)
        server = Server(mock_conn)

        # Then:
        # ... The assigned properties should be assigned
        self.assertIsInstance(server._conn, MockPGServerConnection)
        self.assertIsInstance(server.connection, MockPGServerConnection)
        self.assertIs(server.connection, mock_conn)
        self.assertEqual(server._host, host)
        self.assertEqual(server.host, host)
        self.assertEqual(server._port, port)
        self.assertEqual(server.port, port)
        self.assertEqual(server._maintenance_db_name, dbname)
        self.assertEqual(server.maintenance_db_name, dbname)
        self.assertTupleEqual(server.version, server._conn.server_version)

        # ... Recovery options should be a lazily loaded thing
        self.assertIsInstance(server._recovery_props, NodeLazyPropertyCollection)

        for key, collection in server._child_objects.items():
            # ... The child object collection a NodeCollection
            self.assertIsInstance(collection, NodeCollection)

            # ... There should be a property mapped to the node collection
            prop = getattr(server, inflection.pluralize(key.lower()))
            self.assertIs(prop, collection)

    def test_recovery_properties(self):
        # Setup:
        # NOTE: We're *not* mocking out the template rendering b/c this will verify that there's a template
        # ... Create a mock query execution that will return the properties
        mock_exec_dict = mock.MagicMock(return_value=([], [TestServer.CHECK_RECOVERY_ROW]))

        # ... Create an instance of the class and override the connection
        mock_connection = MockPsycopgConnection('host=host dbname=dbname')
        with mock.patch('psycopg.connect', new=mock.Mock(return_value=mock_connection)):
            pg_connection = PostgreSQLConnection({})
        pg_connection.execute_dict = mock_exec_dict
        obj = Server(pg_connection)

        # If: I retrieve all the values in the recovery properties
        # Then:
        # ... The properties based on the properties should be availble
        self.assertEqual(obj.in_recovery, TestServer.CHECK_RECOVERY_ROW['inrecovery'])
        self.assertEqual(obj.wal_paused, TestServer.CHECK_RECOVERY_ROW['isreplaypaused'])

    def test_maintenance_db(self):
        # Setup:
        # ... Create a server object that has a connection
        obj = Server(MockPGServerConnection(None, name='dbname'))

        # ... Mock out the database lazy loader's indexer
        mock_db = {}
        mock_db_collection = mock.Mock()
        mock_db_collection.__getitem__ = mock.MagicMock(return_value=mock_db)
        obj._child_objects[Database.__name__] = mock_db_collection

        # If: I retrieve the maintenance db for the server
        maintenance_db = obj.maintenance_db

        # Then:
        # ... It must have come from the mock handler
        self.assertIs(maintenance_db, mock_db)
        obj._child_objects[Database.__name__].__getitem__.assert_called_once_with('dbname')

    def test_refresh(self):
        # Setup:
        # ... Create a server object that has a connection
        obj = Server(MockPGServerConnection())

        # ... Mock out the reset methods on the various collections
        obj.databases.reset = mock.MagicMock()
        obj.roles.reset = mock.MagicMock()
        obj.tablespaces.reset = mock.MagicMock()
        obj._recovery_props.reset = mock.MagicMock()

        # If: I refresh the server
        obj.refresh()

        # Then: The collections should have been reset
        obj.databases.reset.assert_called_once()
        obj.roles.reset.assert_called_once()
        obj.tablespaces.reset.assert_called_once()
        obj._recovery_props.reset.assert_called_once()

    def test_urn_base(self):
        # Setup:
        # ... Create a server object that has a connection
        server = Server(MockPGServerConnection())

        # If: I get the URN base for the server
        urn_base = server.urn_base

        # Then: The urn base should match the expected outcome
        urn_base_regex = re.compile(r'//(?P<user>.+)@(?P<host>.+):(?P<port>\d+)')
        urn_base_match = urn_base_regex.match(urn_base)
        self.assertIsNotNone(urn_base_match)
        self.assertEqual(urn_base_match.groupdict()['user'], server.connection.user_name)
        self.assertEqual(urn_base_match.groupdict()['host'], server.host)
        self.assertEqual(urn_base_match.groupdict()['port'], server.port)

    def test_get_obj_by_urn_empty(self):
        # Setup: Create a server object
        server = Server(MockPGServerConnection())

        test_cases = [None, '', '\t \n\r']
        for test_case in test_cases:
            with self.assertRaises(ValueError):
                # If: I get an object by its URN without providing a URN
                # Then: I should get an exception
                server.get_object_by_urn(test_case)

    def test_get_obj_by_urn_wrong_server(self):
        # Setup: Create a server object
        server = Server(MockPGServerConnection())

        with self.assertRaises(ValueError):
            # If: I get an object by its URN with a URN that is invalid for the server
            # Then: I should get an exception
            invalid_urn = '//this@is.the.wrong.urn:456/Database.123/'
            server.get_object_by_urn(invalid_urn)

    def test_get_obj_by_urn_wrong_collection(self):
        # Setup: Create a server object
        server = Server(MockPGServerConnection())

        with self.assertRaises(ValueError):
            # If: I get an object by its URN with a URN that points to an invalid path off the server
            # Then: I should get an exception
            invalid_urn = parse.urljoin(server.urn_base, 'Datatype.123/')
            server.get_object_by_urn(invalid_urn)

    def test_get_obj_by_urn_success(self):
        # Setup: Create a server with a database under it
        server = Server(MockPGServerConnection())
        mock_db = Database(server, 'test_db')
        mock_db._oid = 123
        server._child_objects[Database.__name__] = {123: mock_db}

        # If: I get an object by its URN
        urn = parse.urljoin(server.urn_base, '/Database.123/')
        obj = server.get_object_by_urn(urn)

        # Then: The object I get back should be the same as the object I provided
        self.assertIs(obj, mock_db)
