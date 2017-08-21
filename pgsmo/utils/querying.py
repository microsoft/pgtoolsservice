# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple

from psycopg2.extensions import Column, connection, cursor      # noqa


class ServerConnection:
    """Wrapper for a psycopg2 connection that makes various properties easier to access"""

    def __init__(self, conn: connection):
        """
        Creates a new connection wrapper. Parses version string
        :param conn: PsycoPG2 connection object
        """
        self._conn = conn
        self._dsn_parameters = conn.get_dsn_parameters()

        # Calculate the server version
        version_string = str(conn.server_version)
        self._version: Tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:])
        )

    # PROPERTIES ###########################################################
    @property
    def connection(self) -> connection:
        """The psycopg2 connection that this object wraps"""
        return self._conn

    @property
    def dsn_parameters(self) -> Mapping[str, str]:
        """DSN properties of the underlying connection"""
        return self._dsn_parameters

    @property
    def version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        return self._version

    # METHODS ##############################################################
    def execute_dict(self, query: str, params=None) -> Tuple[List[Column], List[dict]]:
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        cur: cursor = self._conn.cursor()

        try:
            cur.execute(query, params)

            cols: List[Column] = cur.description
            rows: List[dict] = []
            if cur.rowcount > 0:
                for row in cur:
                    row_dict = {cols[ind].name: x for ind, x in enumerate(row)}
                    rows.append(row_dict)

            return cols, rows
        finally:
            cur.close()
