import unittest
from pgsqltoolsservice import connection_service

class TestConnectionService(unittest.TestCase):

    def test_connect(self):
        connection = connection_service.connect('dbname=postgres user=postgres password=password host=MAIRVINE-PC connect_timeout=10')
        self.assertIsNotNone(connection)
        connection.close()

if __name__ == '__main__':
    unittest.main()
