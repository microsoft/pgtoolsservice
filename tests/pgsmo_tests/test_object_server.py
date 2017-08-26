# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import inflection

from pgsmo.objects.node_object import NodeCollection, NodeLazyPropertyCollection
from pgsmo.objects.database.database import Database
from pgsmo.objects.server.server import Server
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


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
        mock_conn = utils.MockConnection(None, name=dbname, host=host, port=port)
        server = Server(mock_conn)

        # Then:
        # ... The assigned properties should be assigned
        self.assertIsInstance(server._conn, ServerConnection)
        self.assertIsInstance(server.connection, ServerConnection)
        self.assertIs(server.connection.connection, mock_conn)
        self.assertEqual(server._host, host)
        self.assertEqual(server.host, host)
        self.assertEqual(server._port, int(port))
        self.assertEqual(server.port, int(port))
        self.assertEqual(server._maintenance_db_name, dbname)
        self.assertEqual(server.maintenance_db_name, dbname)
        self.assertTupleEqual(server.version, server._conn.version)

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
        mock_conn = ServerConnection(utils.MockConnection(None))
        mock_conn.execute_dict = mock_exec_dict
        obj = Server(utils.MockConnection(None))
        obj._conn = mock_conn

        # If: I retrieve all the values in the recovery properties
        # Then:
        # ... The properties based on the properties should be availble
        self.assertEqual(obj.in_recovery, TestServer.CHECK_RECOVERY_ROW['inrecovery'])
        self.assertEqual(obj.wal_paused, TestServer.CHECK_RECOVERY_ROW['isreplaypaused'])

    def test_maintenance_db(self):
        # Setup:
        # ... Create a server object that has a connection
        obj = Server(utils.MockConnection(None, name='dbname'))

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
        obj = Server(utils.MockConnection(None))

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
