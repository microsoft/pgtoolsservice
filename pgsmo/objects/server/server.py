# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional, Tuple                # noqa

from pgsmo.objects.database.database import Database
from pgsmo.objects.tablespace.tablespace import Tablespace
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Server:
    def __init__(self, connection, fetch: bool=True):
        """
        Initializes a server object using the provided connection
        :param connection: psycopg2 connection
        :param fetch: Whether or not to fetch all properties of the server and create child objects, defaults to true
        """
        # Everything we know about the server will be based on the connection
        self._conn = utils.querying.ConnectionWrapper(connection)

        # Declare the server properties
        props = self._conn.connection.get_dsn_parameters()
        self._host: str = props['host']
        self._port: int = int(props['port'])
        self._maintenance_db: str = props['dbname']

        # These properties will be defined later
        self._in_recovery: Optional[bool] = None
        self._wal_paused: Optional[bool] = None

        # Declare the child objects
        self._databases: Optional[List[Database]] = None
        self._tablespaces: Optional[List[Tablespace]] = None

        # Fetch the data for the server
        if fetch:
            self.refresh()

    # PROPERTIES ###########################################################

    @property
    def connection(self):
        """Connection to the server/db that this object will use"""
        return self._conn

    @property
    def host(self) -> str:
        """Hostname of the server"""
        return self._host

    @property
    def in_recovery(self) -> bool:
        """Whether or not the server is in recovery mode"""
        return self._in_recovery

    @property
    def maintenance_db(self) -> str:
        """Name of the database this server's connection is attached to"""
        return self._maintenance_db

    @property
    def port(self) -> int:
        """Port number of the server"""
        return self._port

    @property
    def version(self) -> Tuple[int, int, int]:
        """Tuple representing the server version: (major, minor, patch)"""
        return self._conn.version

    def wal_paused(self) -> bool:
        """Whether or not the Write-Ahead Log (WAL) is paused"""
        return self._wal_paused

    # -CHILD OBJECTS #######################################################
    @property
    def databases(self) -> Optional[List[Database]]:
        """Databases that belong to the server"""
        return self._databases

    @property
    def tablespaces(self) -> Optional[List[Tablespace]]:
        """Tablespaces defined for the server"""
        return self._tablespaces

    # METHODS ##############################################################
    def refresh(self) -> None:
        """Refreshes properties of the server and initializes the child items"""
        self._fetch_recovery_state()
        self._fetch_databases()
        self._fetch_tablespaces()

    # IMPLEMENTATION DETAILS ###############################################

    def _fetch_databases(self) -> None:
        self._databases = Database.get_databases_for_server(self._conn)

    def _fetch_tablespaces(self) -> None:
        self._tablespaces = Tablespace.get_tablespaces_for_server(self._conn)

    def _fetch_recovery_state(self) -> None:
        recovery_check_sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'check_recovery.sql', self._conn.version)
        )

        cols, rows = utils.querying.execute_dict(self._conn, recovery_check_sql)
        if len(rows) > 0:
            self._in_recovery = rows[0]['inrecovery']
            self._wal_paused = rows[0]['isreplaypaused']
        else:
            self._in_recovery = None
            self._wal_paused = None
