# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional               # noqa

import pgsmo.objects.node_object as node
from pgsmo.objects.schema.schema import Schema
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating

TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Database(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection) -> List['Database']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, last_system_oid=0)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Database':
        """
        Creates a new Database object based on the results from a query to lookup databases
        :param conn: Connection used to generate the db info query
        :param kwargs: Optional parameters for the database. Values that can be provided:
        Kwargs:
            did int: Object ID of the database
            name str: Name of the database
            spcname str: Name of the tablespace for the database
            datallowconn bool: Whether or not the database can be connected to
            cancreate bool: Whether or not the database can be created by the current user
            owner int: Object ID of the user that owns the database
        :return: Instance of the Database
        """
        db = cls(conn, kwargs['name'])
        db._oid = kwargs['did']
        db._tablespace = kwargs['spcname']
        db._allow_conn = kwargs['datallowconn']
        db._can_create = kwargs['cancreate']
        db._owner_oid = kwargs['owner']

        return db

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes a new instance of a database
        :param name: Name of the database
        """
        super(Database, self).__init__(conn, name)
        self._is_connected: bool = conn.dsn_parameters.get('dbname') == name

        # Declare the optional parameters
        self._tablespace: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None

        # Declare the child items
        self._schemas: Optional[node.NodeCollection] = None if not self._is_connected else node.NodeCollection(
            lambda: Schema.get_nodes_for_parent(conn)
        )

    # PROPERTIES ###########################################################
    # TODO: Create setters for optional values

    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def tablespace(self) -> str:
        return self._tablespace

    # -CHILD OBJECTS #######################################################
    @property
    def schemas(self) -> node.NodeCollection:
        return self._schemas

    # METHODS ##############################################################
    def create(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def refresh(self):
        """Resets the internal collection of child objects"""
        if self._schemas is not None:
            self._schemas.reset()
