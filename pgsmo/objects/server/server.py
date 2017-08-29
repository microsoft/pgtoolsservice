# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, Mapping, Optional, Tuple                # noqa
from urllib.parse import ParseResult, urlparse, quote_plus       # noqa

from psycopg2.extensions import connection

from pgsmo.objects.node_object import NodeObject, NodeCollection, NodeLazyPropertyCollection
from pgsmo.objects.database.database import Database
from pgsmo.objects.role.role import Role
from pgsmo.objects.tablespace.tablespace import Tablespace
import pgsmo.utils as utils


class Server:
    TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')

    # CONSTRUCTOR ##########################################################
    def __init__(self, conn: connection):
        """
        Initializes a server object using the provided connection
        :param conn: psycopg2 connection
        """
        # Everything we know about the server will be based on the connection
        self._conn: utils.querying.ServerConnection = utils.querying.ServerConnection(conn)

        # Declare the server properties
        props = self._conn.dsn_parameters
        self._host: str = props['host']
        self._port: int = int(props['port'])
        self._maintenance_db_name: str = props['dbname']

        # These properties will be defined later
        self._recovery_props: NodeLazyPropertyCollection = NodeLazyPropertyCollection(self._fetch_recovery_state)

        # Declare the child objects
        self._child_objects: Mapping[str, NodeCollection] = {
            Database.__name__:    NodeCollection(lambda: Database.get_nodes_for_parent(self, None)),
            Role.__name__:        NodeCollection(lambda: Role.get_nodes_for_parent(self, None)),
            Tablespace.__name__:  NodeCollection(lambda: Tablespace.get_nodes_for_parent(self, None))
        }

    # PROPERTIES ###########################################################
    @property
    def connection(self) -> utils.querying.ServerConnection:
        """Connection to the server/db that this object will use"""
        return self._conn

    @property
    def host(self) -> str:
        """Hostname of the server"""
        return self._host

    @property
    def in_recovery(self) -> Optional[bool]:
        """Whether or not the server is in recovery mode. If None, value was not loaded from server"""
        return self._recovery_props.get('inrecovery')

    @property
    def maintenance_db_name(self) -> str:
        """Name of the database this server's connection is connected to"""
        return self._maintenance_db_name

    @property
    def port(self) -> int:
        """Port number of the server"""
        return self._port

    @property
    def version(self) -> Tuple[int, int, int]:
        """Tuple representing the server version: (major, minor, patch)"""
        return self._conn.version

    @property
    def server_type(self) -> str:
        """Server type for distinguishing between standard PG and PG supersets"""
        return 'pg'  # TODO: Determine if a server is PPAS or PG

    @property
    def urn_base(self) -> str:
        """Base of a URN for objects in the tree"""
        user = quote_plus(self.connection.dsn_parameters['user'])
        db = quote_plus(self.maintenance_db_name)
        host = quote_plus(self.host)
        port = quote_plus(str(self.port))
        return f'//{user}@{db}.{host}:{port}/'
        # TODO: Ensure that this formatting works with non-username/password logins

    @property
    def wal_paused(self) -> Optional[bool]:
        """Whether or not the Write-Ahead Log (WAL) is paused. If None, value was not loaded from server"""
        return self._recovery_props.get('isreplaypaused')

    # -CHILD OBJECTS #######################################################
    @property
    def databases(self) -> NodeCollection[Database]:
        """Databases that belong to the server"""
        return self._child_objects[Database.__name__]

    @property
    def maintenance_db(self) -> Database:
        """Database that this server's connection is connected to"""
        return self.databases[self._maintenance_db_name]

    @property
    def roles(self) -> NodeCollection[Role]:
        """Roles that belong to the server"""
        return self._child_objects[Role.__name__]

    @property
    def tablespaces(self) -> NodeCollection[Tablespace]:
        """Tablespaces defined for the server"""
        return self._child_objects[Tablespace.__name__]

    # METHODS ##############################################################
    def get_object_by_urn(self, urn: str) -> NodeObject:
        # Validate that the urn is a full urn
        if urn is None or urn.strip() == '':
            raise ValueError('URN was not provided')    # TODO: Localize?

        parsed_urn: ParseResult = urlparse(urn)
        reconstructed_urn_base = f'//{parsed_urn.netloc}/'
        if reconstructed_urn_base != self.urn_base:
            raise ValueError('Provided URN is not applicable to this server')   # TODO: Localize?

        # Process the first fragment
        class_name, oid, remaining = utils.process_urn(parsed_urn.path)

        # Find the matching collection
        collection = self._child_objects.get(class_name)
        if collection is None:
            raise ValueError(f'URN is invalid: server does not contain {class_name} objects')   # TODO: Localize?

        # Find the matching object
        # TODO: Create a .get method for NodeCollection (see https://github.com/Microsoft/carbon/issues/1713)
        obj = collection[oid]
        return obj.get_object_by_urn(remaining)

    def refresh(self) -> None:
        # Reset child objects
        for collection in self._child_objects.values():
            collection.reset()

        # Reset property collections
        self._recovery_props.reset()

    # IMPLEMENTATION DETAILS ###############################################
    def _fetch_recovery_state(self) -> Dict[str, Optional[bool]]:
        recovery_check_sql = utils.templating.render_template(
            utils.templating.get_template_path(self.TEMPLATE_ROOT, 'check_recovery.sql', self._conn.version)
        )

        cols, rows = self._conn.execute_dict(recovery_check_sql)
        if len(rows) > 0:
            return rows[0]
