# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional, Tuple                # noqa

from psycopg2.extensions import connection

from pgsmo.objects.database.database import Database

from pgsmo.objects.node_object import NodeCollection
from pgsmo.objects.role.role import Role
from pgsmo.objects.tablespace.tablespace import Tablespace
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Server:
    def __init__(self, conn: connection):
        """
        Initializes a server object using the provided connection
        :param conn: psycopg2 connection
        """
        # Everything we know about the server will be based on the connection
        self._conn = utils.querying.ServerConnection(conn)

        # Declare the server properties
        props = self._conn.dsn_parameters
        self._host: str = props['host']
        self._port: int = int(props['port'])
        self._maintenance_db: str = props['dbname']

        # These properties will be defined later
        self._in_recovery: Optional[bool] = None
        self._wal_paused: Optional[bool] = None

        # Declare the child objects
        self._databases: NodeCollection[Database] = NodeCollection(
            lambda: Database.get_nodes_for_parent(self._conn)
        )
        self._roles: NodeCollection[Role] = NodeCollection(
            lambda: Role.get_nodes_for_parent(self._conn)
        )
        self._tablespaces: NodeCollection[Tablespace] = NodeCollection(
            lambda: Tablespace.get_nodes_for_parent(self._conn)
        )

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
    def in_recovery(self) -> Optional[bool]:
        """Whether or not the server is in recovery mode. If None, value was not loaded from server"""
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

    @property
    def wal_paused(self) -> Optional[bool]:
        """Whether or not the Write-Ahead Log (WAL) is paused. If None, value was not loaded from server"""
        return self._wal_paused

    # -CHILD OBJECTS #######################################################
    @property
    def databases(self) -> NodeCollection[Database]:
        """Databases that belong to the server"""
        return self._databases

    @property
    def roles(self) -> NodeCollection[Role]:
        """Roles that belong to the server"""
        return self._roles

    @property
    def tablespaces(self) -> NodeCollection[Tablespace]:
        """Tablespaces defined for the server"""
        return self._tablespaces

    # METHODS ##############################################################

    # IMPLEMENTATION DETAILS ###############################################
    # Commenting out until support for extended properties is added
    # See https://github.com/Microsoft/carbon/issues/1342
    # def _fetch_recovery_state(self) -> None:
    #     recovery_check_sql = utils.templating.render_template(
    #         utils.templating.get_template_path(TEMPLATE_ROOT, 'check_recovery.sql', self._conn.version)
    #     )
    #
    #     cols, rows = self._conn.execute_dict(recovery_check_sql)
    #     if len(rows) > 0:
    #         self._in_recovery = rows[0]['inrecovery']
    #         self._wal_paused = rows[0]['isreplaypaused']
    #     else:
    #         self._in_recovery = None
    #         self._wal_paused = None
