# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.server.server import Server
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


class TestServer(unittest.TestCase):
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

        # ... The optional properties should be assigned to None
        self.assertIsNone(server._in_recovery)
        self.assertIsNone(server.in_recovery)
        self.assertIsNone(server._wal_paused)
        self.assertIsNone(server.wal_paused)

        # ... The child object collections should be assigned to NodeCollections
        self.assertIsInstance(server._databases, NodeCollection)
        self.assertIs(server.databases, server._databases)
        self.assertIsInstance(server._roles, NodeCollection)
        self.assertIs(server.roles, server._roles)
        self.assertIsInstance(server._tablespaces, NodeCollection)
        self.assertIs(server.tablespaces, server._tablespaces)
