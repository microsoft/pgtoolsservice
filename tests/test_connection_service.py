"""Test connection_service.py"""

import unittest
from pgsqltoolsservice.connection_service import ConnectionService

class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_connect_and_disconnect(self):
        """Test that the service connects and disconnects to/from a PostgreSQL server"""
        connection_service = ConnectionService()
        connection_service.connect(
            'dbname=postgres user=postgres password=password host=MAIRVINE-PC connect_timeout=10')
        connection = connection_service.connection
        self.assertIsNotNone(connection)

        connection_service.disconnect()
        connection = connection_service.connection
        self.assertIsNone(connection)

if __name__ == '__main__':
    unittest.main()
