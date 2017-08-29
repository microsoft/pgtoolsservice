# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import pgsmo.utils as pgsmo_utils
import tests.pgsmo_tests.utils as utils


class TestServerConnection(unittest.TestCase):
    def test_server_conn_init(self):
        # Setup: Create a mock connection with an 'interesting' version
        mock_conn = utils.MockConnection(None, version='100216')

        # If: I initialize a server connection
        # noinspection PyTypeChecker
        server_conn = pgsmo_utils.querying.ServerConnection(mock_conn)

        # Then: The properties should be properly set
        self.assertEqual(server_conn._conn, mock_conn)
        self.assertEqual(server_conn.connection, mock_conn)
        expected_dict = {'dbname': 'postgres', 'host': 'localhost', 'port': '25565', 'user': 'postgres'}
        self.assertDictEqual(server_conn._dsn_parameters, expected_dict)
        self.assertDictEqual(server_conn.dsn_parameters, expected_dict)
        self.assertTupleEqual((10, 2, 16), server_conn.version)

    def test_execute_dict_success(self):
        # Setup: Create a mock server connection that will return a result set
        mock_cursor = utils.MockCursor(utils.get_mock_results())
        mock_conn = utils.MockConnection(mock_cursor)
        # noinspection PyTypeChecker
        server_conn = pgsmo_utils.querying.ServerConnection(mock_conn)

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
        # Setup: Create a mock server connection that will raise an exception
        mock_cursor = utils.MockCursor(None, throw_on_execute=True)
        mock_conn = utils.MockConnection(mock_cursor)
        # noinspection PyTypeChecker
        server_conn = pgsmo_utils.querying.ServerConnection(mock_conn)

        # If: I execute a query as a dictionary
        # Then:
        # ... I should get an exception
        with self.assertRaises(Exception):
            server_conn.execute_dict('SELECT * FROM pg_class')

        # ... The cursor should be closed
        mock_cursor.close.assert_called_once()
