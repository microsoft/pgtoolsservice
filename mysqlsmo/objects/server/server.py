# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, List, Mapping, Optional, Tuple, Callable      # noqa
from urllib.parse import ParseResult, urlparse, quote_plus       # noqa

from ossdbtoolsservice.driver import ServerConnection
from smo.common.node_object import NodeObject, NodeCollection, NodeLazyPropertyCollection
import smo.utils as utils
from mysqlsmo.objects.database.database import Database
from mysqlsmo.objects.table.table import Table
from mysqlsmo.objects.view.view import View
from mysqlsmo.objects.procedure.procedure import Procedure
from mysqlsmo.objects.function.function import Function


class Server:
    TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')

    # CONSTRUCTOR ##########################################################
    def __init__(self, conn: ServerConnection, db_connection_callback: Callable[[str], ServerConnection] = None):
        """
        Initializes a server object using the provided connection
        :param conn: a connection object
        """
        # Everything we know about the server will be based on the connection
        self._conn = conn
        self._db_connection_callback = db_connection_callback

        # Declare the server properties
        self._host: str = self._conn.host_name
        self._port: int = self._conn.port
        self._maintenance_db_name: str = self._conn.database_name

        self._child_objects: Mapping[str, NodeCollection] = {
            Database.__name__: NodeCollection(lambda: Database.get_nodes_for_parent(self, None, None))
        }
        # Declare the child objects
        # self._child_objects: Mapping[str, NodeCollection] = {
        #     Database.__name__: NodeCollection(lambda: Database.get_nodes_for_parent(self, None))
        #     # Role.__name__: NodeCollection(lambda: Role.get_nodes_for_parent(self, None)),
        #     # Tablespace.__name__: NodeCollection(lambda: Tablespace.get_nodes_for_parent(self, None)),
        # }
        # self._search_path = NodeCollection(lambda: self._fetch_search_path())

    # PROPERTIES ###########################################################
    @property
    def connection(self) -> ServerConnection:
        """Connection to the server/db that this object will use"""
        return self._conn

    @property
    def db_connection_callback(self):
        """Connection to the server/db that this object will use"""
        return self._db_connection_callback

    @property
    def host(self) -> str:
        """Hostname of the server"""
        return self._host

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
        return self._conn.server_version

    # @property
    # def server_type(self) -> str:
    #     """Server type for distinguishing between standard PG and PG supersets"""
    #     return 'pg'  # TODO: Determine if a server is PPAS or PG

    @property
    def urn_base(self) -> str:
        """Base of a URN for objects in the tree"""
        user = quote_plus(str(self.connection.user_name))
        host = quote_plus(str(self.host))
        port = quote_plus(str(self.port))
        return f'//{user}@{host}:{port}/'
        # TODO: Ensure that this formatting works with non-username/password logins

    # # -CHILD OBJECTS #######################################################
    @property
    def databases(self) -> NodeCollection[Database]:
        """Databases that belong to the server"""
        return self._child_objects[Database.__name__]

    # @property
    # def maintenance_db(self) -> Database:
    #     """Database that this server's connection is connected to"""
    #     return self.databases[self._maintenance_db_name]

    # # @property
    # # def roles(self) -> NodeCollection[Role]:
    # #     """Roles that belong to the server"""
    # #     return self._child_objects[Role.__name__]

    # # @property
    # # def tablespaces(self) -> NodeCollection[Tablespace]:
    # #     """Tablespaces defined for the server"""
    # #     return self._child_objects[Tablespace.__name__]

    # # @property
    # # def search_path(self) -> NodeCollection[str]:
    # #     """
    # #     The search_path for the current role. Defined at the server level as it's a global property,
    # #     and as a collection as it is a list of schema names
    # #     """
    # #     return self._search_path

    def refresh(self) -> None:
        # Reset child objects
        pass

    def get_object(self, object_type: str, metadata):
        """ Retrieve a given object """
        object_map = {
            "Table": lambda met: Table(self, met.name, met.schema),
            "View": lambda met: View(self, met.name, met.schema),
            "Procedure": lambda met: Procedure(self, met.name, met.schema),
            "Function": lambda met: Function(self, met.name, met.schema)
        }
        return object_map[object_type.capitalize()](metadata)
    