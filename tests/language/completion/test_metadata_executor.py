from typing import List, Any
import unittest
from mock import MagicMock, Mock, patch

from pgsmo import Database, NodeCollection, Schema, Server, Table
from pgsqltoolsservice.language.metadata_executor import MetadataExecutor

import tests.pgsmo_tests.utils as utils

MYSCHEMA = 'myschema'
MYSCHEMA2 = 'myschema2'


class TestMetadataExecutor(unittest.TestCase):
    """Methods for testing the MetadataExecutor module"""

    def setUp(self):
        mock_server = Server(utils.MockConnection(None))
        db = Database(mock_server, mock_server.maintenance_db_name)
        mock_server._child_objects[Database.__name__] = self._as_node_collection([db])
        mock_server._search_path = self._as_node_collection([MYSCHEMA])
        self.schema1 = Schema(mock_server, db, MYSCHEMA)
        self.schema2 = Schema(mock_server, db, MYSCHEMA2)
        db._schemas = self._as_node_collection([self.schema1, self.schema2])
        self.mock_server = mock_server
        self.executor: MetadataExecutor = MetadataExecutor(mock_server)
 
    def test_search_path(self):
        self.assertListEqual(self.executor.search_path(), [MYSCHEMA])

    def test_schemata(self):
        self.assertListEqual(self.executor.schemata(), [MYSCHEMA, MYSCHEMA2])

    def test_databases(self):
        self.assertListEqual(self.executor.databases(), [self.mock_server.maintenance_db_name])

    def test_tables(self):
        expected_table_tuples = []
        schema1_tables = []
        schema2_tables = []
        for x in range (0, 3):
            s1_table_name = 's1_t%s' % x
            s2_table_name = 's2_t%s' % x
            schema1_tables.append(Table(self.mock_server, self.schema1, s1_table_name))
            expected_table_tuples.append(tuple([self.schema1.name, s1_table_name]))
            schema2_tables.append(Table(self.mock_server, self.schema2, s2_table_name))
            expected_table_tuples.append(tuple([self.schema2.name, s2_table_name]))
        self.schema1._tables = self._as_node_collection(schema1_tables)
        self.schema2._tables = self._as_node_collection(schema2_tables)
        actual_table_tuples = self.executor.tables()
        self.assertEqual(len(expected_table_tuples), len(actual_table_tuples))
        for expected in expected_table_tuples:
            self.assertTrue(expected in actual_table_tuples)

    # Helper functions ##################################################################
    def _as_node_collection(self, object_list: List[Any]) -> NodeCollection[Any]:
        return NodeCollection(lambda: object_list)
