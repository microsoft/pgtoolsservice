# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple

from psycopg2.extensions import Column, connection, cursor      # noqa


class ConnectionWrapper:
    def __init__(self, conn: connection):
        self._conn = conn
        self._dsn_parameters = conn.get_dsn_parameters()

        # Calculate the server version
        version_string = str(self._conn.server_version)
        self._version: Tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:])
        )

    # PROPERTIES ###########################################################
    @property
    def connection(self) -> connection:
        return self._conn

    @property
    def dsn_parameters(self) -> Mapping[str, str]:
        return self._dsn_parameters

    @property
    def server_type(self) -> str:
        return 'pg'                 # TODO: Determine if a server is PPAS or PG

    @property
    def version(self) -> Tuple[int, int, int]:
        return self._version


def execute_2d_array(conn: ConnectionWrapper, query: str, params=None) -> Tuple[List[Column], List[list]]:
    cur: cursor = conn.connection.cursor()

    try:
        cur.execute(query, params)

        cols: List[Column] = cur.description
        rows: List[list] = []
        if cur.rowcount > 0:
            for row in cur:
                rows.append(row)

        return cols, rows
    finally:
        cur.close()


def execute_dict(conn: ConnectionWrapper, query: str, params=None) -> Tuple[List[Column], List[dict]]:
    cur: cursor = conn.connection.cursor()

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
