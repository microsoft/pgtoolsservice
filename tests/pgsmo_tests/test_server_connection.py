# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import tests.pgsmo_tests.utils as utils
from tests.utils import MockPsycopgConnection
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection


class TestServerConnection(unittest.TestCase):
    def test_server_conn_init(self):
        # Setup: Create a mock connection with an 'interesting' version
        dsn_parameters = {'dbname': 'postgres', 'host': 'localhost', 'port': '25565', 'user': 'postgres'}
        mock_conn = MockPsycopgConnection(dsn_parameters=dsn_parameters)
        mock_conn.server_version = '100216'

        # If: I initialize a server connection
        # noinspection PyTypeChecker
        with mock.patch('psycopg2.connect', new=mock.Mock(return_value=mock_conn)):
            server_conn = PostgreSQLConnection({})

        # Then: The properties should be properly set
        self.assertEqual(server_conn._conn, mock_conn)
        self.assertEqual(server_conn.connection, mock_conn)
        self.assertDictEqual(server_conn._dsn_parameters, dsn_parameters)
        self.assertTupleEqual((10, 2, 16), server_conn.server_version)

    def test_execute_dict_success(self):
        # Setup: Create a mock server connection that will return a result set
        mock_cursor = utils.MockCursor(utils.get_mock_results())
        mock_conn = MockPsycopgConnection(cursor=mock_cursor)

        # noinspection PyTypeChecker
        with mock.patch('psycopg2.connect', new=mock.Mock(return_value=mock_conn)):
            server_conn = PostgreSQLConnection({})

        # If: I execute a query as a dictionary
        results = server_conn.execute_dict('SELECT * FROM pg_class')

        # Then:
        # ... Both the columns and the results should be returned
        self.assertIsInstance(results, tuple)
        self.assertEqual(len(results), 2)

        # ... I should get a list of columns returned to me
        cols = results[0]
        self.assertIsInstance(cols, list)
        self.assertListEqual(cols, mock_cursor.description)

        # ... I should get the results formatted as a list of dictionaries
        rows = results[1]
        self.assertIsInstance(rows, list)
        for idx, row in enumerate(rows):
            self.assertDictEqual(row, mock_cursor._results[1][idx])

        # ... The cursor should be closed
        mock_cursor.close.assert_called_once()

    def test_execute_dict_fail(self):
        # Setup: Create a mock psycopg connection that will raise an exception
        mock_cursor = utils.MockCursor(None, throw_on_execute=True)
        mock_conn = MockPsycopgConnection(cursor=mock_cursor)
        # noinspection PyTypeChecker
        with mock.patch('psycopg2.connect', new=mock.Mock(return_value=mock_conn)):
            server_conn = PostgreSQLConnection({})

        # If: I execute a query as a dictionary
        # Then:
        # ... I should get an exception
        with self.assertRaises(Exception):
            server_conn.execute_dict('SELECT * FROM pg_class')

        # ... The cursor should be closed
        mock_cursor.close.assert_called_once()
