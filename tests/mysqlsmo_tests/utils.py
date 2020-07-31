import unittest
import unittest.mock as mock
from typing import List, Optional, Tuple

from pymysql.err import DatabaseError

from ossdbtoolsservice.driver.types.pymysql_driver import MySQLConnection
from tests.utils import MockPyMySQLConnection


class MockCursor:
    def __init__(self, results: Optional[Tuple[List, List[dict]]] = None, throw_on_execute=False):
        # Setup the results, that will change value once the cursor is executed
        self._results = results
        self._throw_on_execute = throw_on_execute

        # Define mocks for the methods of the cursor
        self.execute = mock.MagicMock(side_effect=self._execute)
        self.close = mock.MagicMock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _execute(self, query, params=None):
        # Raise error if that was expected, otherwise set the output
        if self._throw_on_execute:
            raise DatabaseError()

    def fetchall(self):
        return self._results


class MockMySQLServerConnection(MySQLConnection):
    '''Class used to mock MySQL ServerConnection object for testing'''

    def __init__(
            self,
            cur: Optional[MockCursor] = None,
            connection: Optional[MockPyMySQLConnection] = None,
            version: str = '5.7.29-log',
            name: str = 'mysql',
            host: str = 'localhost',
            port: str = '25565',
            user: str = 'mysql'):

        # Setup mocks for the connection
        self.close = mock.MagicMock()
        self.cursor = mock.MagicMock(return_value=cur)

        # if no cursor is passed, create default one
        if not cur:
            # MySQLConnection constructor executes a query to find server version
            cur = MockCursor(results=[[version]])

        # if no mock mysql connection passed, create default one
        if not connection:
            connection = MockPyMySQLConnection(cursor=cur, parameters={
                'database': name, 'host': host, 'port': port, 'user': user})

        # mock pymysql.connect call in MySQLConnection.__init__ to return mock pymysql connection
        with mock.patch('pymysql.connect', mock.Mock(return_value=connection)):
            super().__init__({"host": host, "user": user, "port": port, "database": name})
