# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock
from collections.abc import Generator
from typing import Any, Optional

from psycopg import Column, DatabaseError, connection

from ossdbtoolsservice.connection.core.server_connection import (
    PG_CANCELLATION_QUERY,
    Params,
    ServerConnection,
)
from pgsmo import Server
from smo.common.node_object import NodeCollection, NodeObject
from tests.utils import MockPsycopgConnection


# MOCK NODE OBJECT #########################################################
class MockNodeObject(NodeObject):
    @classmethod
    def _from_node_query(cls, root_server: Server, parent: Optional[NodeObject], **kwargs):
        pass

    def __init__(self, root_server: Server, parent: Optional[NodeObject], name: str):
        super().__init__(root_server, parent, name)

    @classmethod
    def _template_root(cls, root_server: Server):
        return "template_root"

    @property
    def template_vars(self) -> str:
        pass

    def get_database_node(self):
        return mock.MagicMock(datlastsysoid=None)


# MOCK CONNECTION ##########################################################


def get_mock_columns(col_count: int) -> list[Column]:
    return [
        Column(f"column{i}", None, 10, 10, None, None, True) for i in range(0, col_count + 1)
    ]


def get_named_mock_columns(col_names: list[str]) -> list[Column]:
    return [Column(x, None, 10, 10, None, None, True) for x in col_names]


def get_mock_results(
    col_count: int = 5, row_count: int = 5
) -> tuple[list[Column], list[dict]]:
    rows = []
    cols = get_mock_columns(col_count)
    for i in range(0, len(cols)):
        # Add the column to the rows
        for j in range(0, row_count + 1):
            if len(rows) >= j:
                rows.append({})

            rows[j][cols[i].name] = f"value{j}.{i}"

    return cols, rows


class MockCursor:
    def __init__(
        self,
        results: Optional[tuple[list[Column], list[dict]]],
        throw_on_execute: bool = False,
        mogrified_value: str = "SomeQuery",
    ) -> None:
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

    def __iter__(self) -> Generator[list[Any], Any, None]:
        # If we haven't read yet, raise an error
        # Or if we have read but we're past the end of the list, raise an error
        if not self._results:
            raise StopIteration
        if not self._has_been_read or self._iter_index > len(self._results[1]):
            raise StopIteration

        # From python 3.6+ this dicts preserve order, so this isn't an issue
        yield list(self._results[1][self._iter_index].values())
        self._iter_index += 1

    def __enter__(self) -> "MockCursor":
        return self

    def __exit__(self) -> None:
        pass

    @property
    def mogrified_value(self) -> str:
        return self._mogrified_value

    def _execute(self, query: str, params: Params | None = None) -> None:
        # Raise error if that was expected, otherwise set the output
        if self._throw_on_execute:
            raise DatabaseError()

        self.description = self._results[0]
        self.rowcount = len(self._results[1])
        self._has_been_read = True


class MockPGServerConnection(ServerConnection):
    """Class used to mock PGSQL ServerConnection objects for testing"""

    def __init__(
        self,
        cur: Optional[MockCursor] = None,
        connection: Optional[MockPsycopgConnection] = None,
        version: str = "131001",
        name: str = "postgres",
        host: str = "localhost",
        port: str = "25565",
        user: str = "postgres",
    ):
        # Setup mocks for the connection
        self.close = mock.MagicMock()
        self.cursor = mock.MagicMock(return_value=cur)

        self._backend_pid = 0

        # if no mock pyscopg connection passed, create default one
        if not connection:
            connection = MockPsycopgConnection(
                cursor=cur,
                dsn_parameters=f"host={host} dbname={name} user={user} port={port}",
            )

        # mock psycopg.connect call in ServerConnection.__init__
        # to return mock psycopg connection
        super().__init__(
            connection=connection,
        )

    @property
    def connection(self) -> connection:
        """Returns the underlying connection"""
        return self._conn

    @property
    def cancellation_query(self) -> str:
        """Returns a SQL command to end the current query execution process"""
        return PG_CANCELLATION_QUERY.format(0)

    @property
    def backend_pid(self) -> int:
        """Returns the backend process ID"""
        return self._backend_pid


# OBJECT TEST HELPERS ######################################################


def assert_node_collection(prop: any, attrib: any):
    test_case = unittest.TestCase("__init__")
    test_case.assertIsInstance(attrib, NodeCollection)
    test_case.assertIs(prop, attrib)


def assert_threeway_equals(target: any, attrib: any, prop: any):
    test_case = unittest.TestCase("__init__")
    test_case.assertEqual(attrib, target)
    test_case.assertEqual(prop, target)


def assert_is_not_none_or_whitespace(target: str):
    test_case = unittest.TestCase("__init__")
    test_case.assertIsNotNone(target)
    test_case.assertIsInstance(target, str)
    test_case.assertNotEqual(target.strip(), "")
