# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional, Tuple
import unittest.mock as mock

from psycopg2 import DatabaseError
from psycopg2.extensions import Column, connection, cursor


def get_mock_results(col_count: int=5, row_count: int=5) -> Tuple[List[Column], List[dict]]:
    rows = []
    cols = []
    for i in range(0, col_count+1):
        # Build a column
        col = Column(f'column{i}', None, 10, 10, None, None, True)
        cols.append(col)

        # Add the column to the rows
        for j in range(0, row_count+1):
            if len(rows) >= j:
                rows.append({})

            rows[j][col.name] = f'value{j}.{i}'

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


class MockConnection:
    def __init__(self, cur: Optional[MockCursor], version: str='90602'):
        # Setup the properties
        self.server_version = version

        # Setup mocks for the connection
        self.close = mock.MagicMock()
        self.cursor = mock.MagicMock(return_value=cur)
        self.get_dsn_parameters = mock.MagicMock(return_value={'dbname': 'postgres', 'host': 'localhost'})
