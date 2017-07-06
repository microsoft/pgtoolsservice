# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, List, Optional, Tuple
import unittest
import unittest.mock as mock

from psycopg2 import DatabaseError
from psycopg2.extensions import Column, connection, cursor

from pgsmo.objects.node_object import NodeObject, NodeCollection
from pgsmo.utils.querying import ServerConnection


# MOCK CONNECTION ##########################################################
def get_mock_columns(col_count: int) -> List[Column]:
    return [Column(f'column{i}', None, 10, 10, None, None, True) for i in range(0, col_count+1)]


def get_named_mock_columns(col_names: List[str]) -> List[Column]:
    return [Column(x, None, 10, 10, None, None, True) for x in col_names]


def get_mock_results(col_count: int=5, row_count: int=5) -> Tuple[List[Column], List[dict]]:
    rows = []
    cols = get_mock_columns(col_count)
    for i in range(0, len(cols)):
        # Add the column to the rows
        for j in range(0, row_count+1):
            if len(rows) >= j:
                rows.append({})

            rows[j][cols[i].name] = f'value{j}.{i}'

    return cols, rows


class MockCursor:
    def __init__(self, results: Optional[Tuple[List[Column], List[dict]]], throw_on_execute=False):
        # Setup the results, that will change value once the cursor is executed
        self.description = None
        self.rowcount = None
        self._results = results
        self._throw_on_execute = throw_on_execute

        # Define iterator state
        self._has_been_read = False
        self._iter_index = 0

        # Define mocks for the methods of the cursor
        self.execute = mock.MagicMock(side_effect=self._execute)
        self.close = mock.MagicMock()

    def __iter__(self):
        # If we haven't read yet, raise an error
        # Or if we have read but we're past the end of the list, raise an error
        if not self._has_been_read or self._iter_index > len(self._results[1]):
            raise StopIteration

        # From python 3.6+ this dicts preserve order, so this isn't an issue
        yield list(self._results[1][self._iter_index].values())
        self._iter_index += 1

    def _execute(self, query, params):
        # Raise error if that was expected, otherwise set the output
        if self._throw_on_execute:
            raise DatabaseError()

        self.description = self._results[0]
        self.rowcount = len(self._results[1])
        self._has_been_read = True


class MockConnection(connection):
    def __init__(
            self,
            cur: Optional[MockCursor],
            version: str='90602',
            name: str='postgres',
            host: str='localhost',
            port: str='25565'):
        # Setup the properties
        self._server_version = version

        # Setup mocks for the connection
        self.close = mock.MagicMock()
        self.cursor = mock.MagicMock(return_value=cur)

        dsn_params = {'dbname': name, 'host': host, 'port': port}
        self.get_dsn_parameters = mock.MagicMock(return_value=dsn_params)

    @property
    def server_version(self):
        return self._server_version


# OBJECT TEST HELPERS ######################################################
def get_nodes_for_parent_base(class_, data: dict, get_nodes_for_parent: Callable, validate_obj: Callable):
    # Setup: Create a mockup server connection
    mock_cur = MockCursor((get_named_mock_columns(list(data.keys())), [data for i in range(0, 6)]))
    mock_conn = ServerConnection(MockConnection(mock_cur))

    # ... Create a mock template renderer
    mock_render = mock.MagicMock(return_value="SQL")
    mock_template_path = mock.MagicMock(return_value="path")

    # ... Create a testcase for calling asserts with
    test_case = unittest.TestCase('__init__')

    # ... Patch the templating
    with mock.patch(class_.__module__ + '.templating.render_template', mock_render, create=True):
        with mock.patch(class_.__module__ + '.templating.get_template_path', mock_template_path, create=True):
            # If: ask for a collection of nodes
            output = get_nodes_for_parent(mock_conn)

            # Then:
            # ... The output should be a list of objects
            test_case.assertIsInstance(output, list)

            for obj in output:
                # ... The object must be the class that was passed in
                test_case.assertIsInstance(obj, class_)

                # ... Call the validator on the object
                validate_obj(obj, mock_conn)


def from_node_query_base(class_, data: dict, validate_obj: Callable):
    # If: I create a new object from a node row
    mock_conn = ServerConnection(MockConnection(None))
    obj = class_._from_node_query(mock_conn, **data)

    # Then:
    # ... The returned object must be an instance of the class
    test_case = unittest.TestCase('__init__')
    test_case.assertIsInstance(obj, NodeObject)
    test_case.assertIsInstance(obj, class_)

    # ... Call the validation function
    validate_obj(obj, mock_conn)


def init_base(class_, props: List[str], collections: List[str], custom_validation: Callable=None):
    # If: I create an instance of the provided class
    mock_conn = ServerConnection(MockConnection(None))
    name = 'test'
    obj = class_(mock_conn, name)

    validate_init(class_, name, mock_conn, obj, props, collections, custom_validation)


def validate_init(class_, name, mock_conn, obj, props: List[str], collections: List[str],
                  custom_validation: Callable=None):
    # Then:
    # ... The object must be of the type that was provided
    test_case = unittest.TestCase('__init__')
    test_case.assertIsInstance(obj, NodeObject)
    test_case.assertIsInstance(obj, class_)

    # ... The NodeObject basic properties should be set up appropriately
    test_case.assertIs(obj._conn, mock_conn)
    test_case.assertEqual(obj._name, name)
    test_case.assertEqual(obj.name, name)
    test_case.assertIsNone(obj._oid)
    test_case.assertIsNone(obj.oid)

    # ... The rest of the properties should be none
    for prop in props:
        test_case.assertIsNone(getattr(obj, prop))

    # ... The child properties should be assigned to node collections
    for coll in collections:
        test_case.assertIsInstance(getattr(obj, coll), NodeCollection)

    # ... Run the custom validation
    if custom_validation is not None:
        custom_validation(obj)