# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional               # noqa

import pgsmo.objects.node_object as node
from pgsmo.objects.schema.schema import Schema
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating

class Database(node.NodeObject):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

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
        db._oid = kwargs['oid']
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
        self._version = conn.version
        self._connection = conn

        # Declare the optional parameters
        self._tablespace: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None

        # Declare the child items
        self._schemas: Optional[node.NodeCollection[Schema]] = None
        if self._is_connected:
            self._schemas = self._register_child_collection(lambda: Schema.get_nodes_for_parent(conn, self))

    # PROPERTIES ###########################################################
    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def tablespace(self) -> str:
        return self._tablespace

    @property
    def oid(self) -> Optional[int]:
        return self._oid

    @property
    def encoding(self) -> str:
        try:
            encoding = self._full_properties['encoding']
        except:
            encoding = ""
        return encoding

    @property 
    def template(self) -> str:
        try:
            template = self._full_properties['template']
        except:
            template = ""
        return template

    @property 
    def datcollate(self):
        try:
            datcollate = self._full_properties['datcollate']
        except:
            datcollate = ""
        return datcollate

    @property
    def datctype(self):
        try:
            datctype = self._full_properties['datctype']
        except:
            datctype = ""
        return datctype

    @property
    def spcname(self):
        try:
            spcname = self._full_properties['spcname']
        except:
            spcname = ""
        return spcname

    @property
    def datconnlimit(self):
        try:
            datconnlimit = self._full_properties['datconnlimit']
        except:
            datconnlimit = ""
        return datconnlimit

    # -CHILD OBJECTS #######################################################
    @property
    def schemas(self) -> node.NodeCollection[Schema]:
        return self._schemas

    # HELPER METHODS #######################################################

    def create_query_data(self, connection: querying.ServerConnection) -> dict:

        data = {"data": {
            "name": self.name,
            "encoding": self.encoding,
            "template": self.template,
            "datcollate": self.datcollate,
            "datctype": self.datctype,
            "datconnlimit": self.datconnlimit,
            "spcname": self.spcname
        }}
        return data

    # METHODS ##############################################################

    def create(self, connection: querying.ServerConnection):
        data = self.create_query_data(connection)
        template_root = self._template_root(connection)
        template_path = templating.get_template_path(template_root, 'create.sql', connection.version)
        create_template = templating.render_template(template_path, **data)
        return create_template

    def update(self):
        pass

    def delete(self):
        pass

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT
