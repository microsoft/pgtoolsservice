# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional, Tuple
import unittest
import unittest.mock as mock

from psycopg2 import DatabaseError
from psycopg2.extensions import Column

from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection
from pgsmo import Server
from smo.common.node_object import NodeCollection, NodeObject
from tests.utils import MockPsycopgConnection

# MOCK NODE OBJECT #########################################################
class MockNodeObject(NodeObject):
    @classmethod
    def _from_node_query(cls, root_server: Server, parent: Optional[NodeObject], **kwargs):
        pass

    def __init__(self, root_server: Server, parent: Optional[NodeObject], name: str):
        super(MockNodeObject, self).__init__(root_server, parent, name)

    @classmethod
    def _template_root(cls, root_server: Server):
        return 'template_root'

    @property
    def template_vars(self) -> str:
        pass

    def get_database_node(self):
        return mock.MagicMock(datlastsysoid=None)

# MOCK CONNECTION ##########################################################


def get_mock_columns(col_count: int) -> List[Column]:
    return [Column(f'column{i}', None, 10, 10, None, None, True) for i in range(0, col_count + 1)]


def get_named_mock_columns(col_names: List[str]) -> List[Column]:
    return [Column(x, None, 10, 10, None, None, True) for x in col_names]


def get_mock_results(col_count: int = 5, row_count: int = 5) -> Tuple[List[Column], List[dict]]:
    rows = []
    cols = get_mock_columns(col_count)
    for i in range(0, len(cols)):
        # Add the column to the rows
        for j in range(0, row_count + 1):
            if len(rows) >= j:
                rows.append({})

            rows[j][cols[i].name] = f'value{j}.{i}'

    return cols, rows


class MockCursor:
    def __init__(self, results: Optional[Tuple[List[Column], List[dict]]], throw_on_execute=False, mogrified_value='SomeQuery'):
        # Setup the results, that will change value once the cursor is executed
        self.description = None
        self.rowcount = None
        self._results = results
        self._throw_on_execute = throw_on_execute
        self._mogrified_value = mogrified_value
        # Define iterator state
        self._has_been_read = False
        self._iter_index = 0

        # Define mocks for the methods of the cursor
        self.execute = mock.MagicMock(side_effect=self._execute)
        self.close = mock.MagicMock()
        self.mogrify = mock.Mock(return_value=self._mogrified_value)

    def __iter__(self):
        # If we haven't read yet, raise an error
        # Or if we have read but we're past the end of the list, raise an error
        if not self._has_been_read or self._iter_index > len(self._results[1]):
            raise StopIteration

        # From python 3.6+ this dicts preserve order, so this isn't an issue
        yield list(self._results[1][self._iter_index].values())
        self._iter_index += 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @property
    def mogrified_value(self):
        return self._mogrified_value

    def _execute(self, query, params=None):
        # Raise error if that was expected, otherwise set the output
        if self._throw_on_execute:
            raise DatabaseError()

        self.description = self._results[0]
        self.rowcount = len(self._results[1])
        self._has_been_read = True


class MockPGServerConnection(PostgreSQLConnection):
    '''Class used to mock PGSQL ServerConnection objects for testing'''
    def __init__(
        self,
        cur: Optional[MockCursor] = None,
        connection: Optional[MockPsycopgConnection] = None,
        version: str = '90602',
        name: str = 'postgres',
        host: str = 'localhost',
        port: str = '25565',
        user: str = 'postgres'):

        # Setup mocks for the connection
        self.close = mock.MagicMock()
        self.cursor = mock.MagicMock(return_value=cur)

        # if no mock pyscopg connection passed, create default one
        if not connection:
            connection = MockPsycopgConnection(cursor=cur, dsn_parameters={
                'dbname': name, 'host': host, 'port': port, 'user': user})

        # mock psycopg2.connect call in PostgreSQLConnection.__init__ to return mock psycopg connection
        with mock.patch('psycopg2.connect', mock.Mock(return_value=connection)):
            super().__init__({"host_name": host, "user_name": user, "port": port, "database_name": name})

# OBJECT TEST HELPERS ######################################################
def assert_node_collection(prop: any, attrib: any):
    test_case = unittest.TestCase('__init__')
    test_case.assertIsInstance(attrib, NodeCollection)
    test_case.assertIs(prop, attrib)


def assert_threeway_equals(target: any, attrib: any, prop: any):
    test_case = unittest.TestCase('__init__')
    test_case.assertEqual(attrib, target)
    test_case.assertEqual(prop, target)


def assert_is_not_none_or_whitespace(target: str):
    test_case = unittest.TestCase('__init__')
    test_case.assertIsNotNone(target)
    test_case.assertIsInstance(target, str)
    test_case.assertNotEqual(target.strip(), '')
