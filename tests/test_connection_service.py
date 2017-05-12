# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection_service.py"""

import unittest

from pgsqltoolsservice.connection_service import ConnectionInfo, ConnectionService


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect_and_disconnect(self):
        """Test that the service connects and disconnects to/from a PostgreSQL server"""
        connection_service = ConnectionService(None)
        connection_service.connect(ConnectionInfo(
            None,
            {'options': {
                'connectionString': 'dbname=postgres user=postgres password=password host=MAIRVINE-PC connect_timeout=10'}},
            None))
        connection = connection_service.connection
        self.assertIsNotNone(connection)

        connection_service.disconnect()
        connection = connection_service.connection
        self.assertIsNone(connection)


if __name__ == '__main__':
    unittest.main()
