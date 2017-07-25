# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeCollection, NodeLazyPropertyCollection
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
        self.assertEqual(server._maintenance_db, dbname)
        self.assertEqual(server.maintenance_db, dbname)
        self.assertTupleEqual(server.version, server._conn.version)

        # ... Recovery options should be a lazily loaded thing
        self.assertIsInstance(server._recovery_props, NodeLazyPropertyCollection)

        # ... The child object collections should be assigned to NodeCollections
        self.assertIsInstance(server._databases, NodeCollection)
        self.assertIs(server.databases, server._databases)
        self.assertIsInstance(server._roles, NodeCollection)
        self.assertIs(server.roles, server._roles)
        self.assertIsInstance(server._tablespaces, NodeCollection)
        self.assertIs(server.tablespaces, server._tablespaces)

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
