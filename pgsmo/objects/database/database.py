# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional               # noqa

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
from pgsmo.objects.schema.schema import Schema
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Database(node.NodeObject):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Database':
        """
        Creates a new Database object based on the results from a query to lookup databases
        :param server: Server that owns the database
        :param parent: Parent object of the database. Should always be None
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
        db = cls(server, kwargs['name'])
        db._oid = kwargs['oid']
        db._tablespace = kwargs['spcname']
        db._allow_conn = kwargs['datallowconn']
        db._can_create = kwargs['cancreate']
        db._owner_oid = kwargs['owner']

        return db

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes a new instance of a database
        :param server: Server that owns the database.
        :param name: Name of the database
        """

        super(Database, self).__init__(server, None, name)
        self._is_connected: bool = server.maintenance_db_name == name

        # Declare the optional parameters
        self._tablespace: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None

        # Declare the child items
        self._schemas: Optional[node.NodeCollection[Schema]] = None
        if self._is_connected:
            self._schemas = self._register_child_collection(lambda: Schema.get_nodes_for_parent(self._server, self))

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def tablespace(self) -> str:
        return self._tablespace

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def encoding(self) -> str:
        return self._full_properties.get("encoding", "")

    @property
    def template(self) -> str:
        return self._full_properties.get("template", "")

    @property
    def datcollate(self):
        return self._full_properties.get("datcollate", "")

    @property
    def datctype(self):
        return self._full_properties.get("datctype", "")

    @property
    def spcname(self):
        return self._full_properties.get("spcname", "")

    @property
    def datconnlimit(self):
        return self._full_properties.get("datconnlimit", "")

    # -CHILD OBJECTS #######################################################
    @property
    def schemas(self) -> node.NodeCollection[Schema]:
        return self._schemas

    # METHODS ##############################################################

    def create_script(self) -> str:
        """ Function to retrieve create scripts for a database """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(query_file, data)

    def delete_script(self) -> str:
        """ Function to retrieve delete scripts for a database """
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(query_file, data)

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT

    # HELPER METHODS #######################################################

    # QUERY INPUT METHODS ##################################################
    def _create_query_data(self) -> dict:
        """ Return the data input for create query """
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

    def _delete_query_data(self) -> dict:
        """ Return the data input for delete query """
        data = {
            "did": self._oid,
            "datname": self._name
        }
        return data
