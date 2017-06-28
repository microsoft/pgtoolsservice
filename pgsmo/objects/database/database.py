# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional               # noqa

import pgsmo.objects.schema.schema as schema
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Database:
    @staticmethod
    def get_databases_for_server(conn: utils.querying.ServerConnection, fetch: bool=True) -> List['Database']:
        # Execute query to get list of databases
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version),
            last_system_oid=0
        )
        cols, rows = conn.execute_dict(sql)

        return [Database._from_node_query(conn, row['did'], row['name'], fetch, **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ServerConnection, db_did: int, db_name: str, fetch: bool=True,
                         **kwargs):
        """
        Creates a new Database object based on the results from a query to lookup databases
        :param conn: Connection used to generate the db info query
        :param db_did: Object ID of the database
        :param db_name: Name of the database
        :param kwargs: Optional parameters for the database. Values that can be provided:
        Kwargs:
            spcname str: Name of the tablespace for the database
            datallowconn bool: Whether or not the database can be connected to
            cancreate bool: Whether or not the database can be created by the current user
            owner int: Object ID of the user that owns the database
        :return: Instance of the Database
        """
        db = cls(db_name)

        # Assign the mandatory properties
        db._did = db_did
        db._conn = conn
        db._is_connected = db_name == conn.dsn_parameters.get('dbname')

        # Assign the optional properties
        db._tablespace = kwargs.get('spcname')
        db._allow_conn = kwargs.get('datallowconn')
        db._can_create = kwargs.get('cancreate')
        db._owner_oid = kwargs.get('owner')

        # If fetch was requested, do complete refresh
        if fetch and db._is_connected:
            db.refresh()

        return db

    def __init__(self, name: str):
        """
        Initializes a new instance of a database
        :param name: Name of the database
        """
        self._name: str = name
        self._is_connected: bool = False

        # Declare the optional parameters
        self._conn: utils.querying.ServerConnection = None
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
