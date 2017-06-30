# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional               # noqa

import pgsmo.objects.node_object as node
import pgsmo.objects.schema.schema as schema
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Database:
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper) -> List['Database']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Database':
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
        db = cls(kwargs['name'])
        db._conn = conn
        db._did = kwargs['did']
        db._is_connected = kwargs['name'] == conn.dsn_parameters.get('dbname')
        db._tablespace = kwargs['spcname']
        db._allow_conn = kwargs['datallowconn']
        db._can_create = kwargs['cancreate']
        db._owner_oid = kwargs['owner']

        return db

    def __init__(self, name: str):
        """
        Initializes a new instance of a database
        :param name: Name of the database
        """
        self._name: str = name
        self._is_connected: bool = False

        # Declare the optional parameters
        self._conn: utils.querying.ConnectionWrapper = None
        self._did: Optional[int] = None
        self._tablespace: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None

        # Declare the child items
        self._schemas: List[schema.Schema] = None

    # PROPERTIES ###########################################################
    # TODO: Create setters for optional values

    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def name(self) -> str:
        return self._name

    @property
    def oid(self) -> int:
        return self._did

    @property
    def schemas(self) -> List[schema.Schema]:
        return self._schemas

    @property
    def tablespace(self) -> str:
        return self._tablespace

    # METHODS ##############################################################

    def refresh(self):
        self._fetch_properties()
        self._fetch_schemas()

    def create(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    # IMPLEMENTATION DETAILS ###############################################
    def _fetch_properties(self):
        pass

    def _fetch_schemas(self):
        self._schemas = schema.Schema.get_schemas_for_database(self._conn)
