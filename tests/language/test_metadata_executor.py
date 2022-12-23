# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from typing import Any, List
from unittest import mock

import mysql

import tests.mysqlsmo_tests.utils as utils
from ossdbtoolsservice.language.metadata_executor import MetadataExecutor
from mysqlsmo import Database, Server
from smo.common.node_object import NodeCollection


class MockCursor:
    """Class used to mock mysql cursor objects for testing"""

    def __init__(self, query_results):
        self.query_results = query_results
        self.execute = mock.Mock(side_effect=self.execute_success_side_effects)
        self.fetchall = mock.Mock(return_value=query_results)
        self.close = mock.Mock()
        self.connection = mock.Mock()
        self.description = None
        self.rowcount = -1
        self.mogrify = mock.Mock(side_effect=self._mogrify)
        # Define iterator state
        self._has_been_read = False

    def __iter__(self):
        # If we haven't read yet, raise an error
        # Or if we have read but we're past the end of the list, raise an error
        if not self._has_been_read:
            raise StopIteration

        # From python 3.6+ this dicts preserve order, so this isn't an issue
        for x in self.query_results:
            yield x

    def execute_success_side_effects(self, *args):
        """Set up dummy results for query execution success"""
        self.connection.notices = ["NOTICE: foo", "DEBUG: bar"]
        self.description = []
        self._has_been_read = True

    def execute_failure_side_effects(self, *args):
        """Set up dummy results and raise error for query execution failure"""
        self.connection.notices = ["NOTICE: foo", "DEBUG: bar"]
        raise mysql.DatabaseError()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _mogrify(self, *args, **kwargs):
        return args[0].format(args[1:])


class TestMetadataExecutor(unittest.TestCase):
    """Methods for testing the MetadataExecutor module"""

    def setUp(self):
        mock_server = Server(utils.MockMySQLServerConnection())
        db = Database(mock_server, mock_server.maintenance_db_name)
        mock_server._child_objects[Database.__name__] = self._as_node_collection([db])
        self.mock_server = mock_server
        self.executor: MetadataExecutor = MetadataExecutor(mock_server)

    def test_databases(self):
        self.assertListEqual(self.executor.databases(), [self.mock_server.maintenance_db_name])

    def test_tables(self):
        # Given 2 tables in the database
        expected_table_tuples = []
        for x in range(0, 3):
            s1_table_name = 's1_t%s' % x
            s2_table_name = 's2_t%s' % x
            expected_table_tuples.append(tuple([s1_table_name]))
            expected_table_tuples.append(tuple([s2_table_name]))

        cursor = MockCursor(expected_table_tuples)
        mock_server = Server(utils.MockMySQLServerConnection(cursor))
        executor: MetadataExecutor = MetadataExecutor(mock_server)
        # When I query tables
        actual_table_tuples = executor.tables()

        # I expect to get 2 tables from the executor
        self.assertEqual(len(expected_table_tuples), len(actual_table_tuples))
        for expected in expected_table_tuples:
            self.assertTrue(expected in actual_table_tuples)

    # Helper functions ##################################################################
    def _as_node_collection(self, object_list: List[Any]) -> NodeCollection[Any]:
        return NodeCollection(lambda: object_list)
