# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional, Union             # noqa

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

        # Declare the basic properties
        self._tablespace_name: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None

        # Declare the child items
        self._schemas = None
        self._full_properties = None
        if self._is_connected:
            self._schemas = self._register_child_collection(lambda: Schema.get_nodes_for_parent(conn))
            self._full_properties = self._register_property_collection(self._full_properties_generator)

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES
    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def tablespace_name(self) -> Optional[str]:
        return self._tablespace_name

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def acl(self) -> Optional[str]:
        return self._get_full_property('acl')

    @property
    def character_type(self) -> Optional[str]:
        return self._get_full_property('datctype')

    @property
    def collation(self) -> Optional[str]:
        return self._get_full_property('datcollate')

    @property
    def comments(self) -> Optional[str]:
        return self._get_full_property('comments')

    @property
    def connection_limit(self) -> Optional[int]:
        return self._get_full_property('datconnlimit')

    @property
    def default_tablespace_name(self) -> Optional[str]:
        return self._get_full_property('default_tablespace')

    @property
    def encoding(self) -> Optional[str]:
        return self._get_full_property('encoding')

    @property
    def function_acl(self) -> Optional[str]:
        return self._get_full_property('funcacl')

    @property
    def is_template(self) -> Optional[bool]:
        return self._get_full_property('is_template')

    @property
    def owner_name(self) -> Optional[str]:
        return self._get_full_property('datowner')

    @property
    def sequence_acl(self) -> Optional[str]:
        return self._get_full_property('seqacl')

    @property
    def table_acl(self) -> Optional[str]:
        return self._get_full_property('tblacl')

    @property
    def tablespace_oid(self) -> Optional[int]:
        return self._get_full_property('spcoid')

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

    # IMPLEMENTATION DETAILS ###############################################
    def _full_properties_generator(self):
        """
        Looks up full properties of an object using the properties.sql template
        :return:
        """
        sql = templating.render_template(
            templating.get_template_path(TEMPLATE_ROOT, 'properties.sql', self._conn.version),
            did=self._oid
        )
        cols, rows = self._conn.execute_dict(sql)

        if len(rows) > 0:
            return rows[0]
        else:
            return None

    def _get_full_property(self, property_name: str) -> Optional[Union[str, int, bool]]:
        return self._full_properties[property_name] if self._is_connected else None
