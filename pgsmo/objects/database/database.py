# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional               # noqa

from smo.common.node_object import NodeCollection, NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete
from pgsmo.objects.server import server as s    # noqa
from pgsmo.objects.schema.schema import Schema
import smo.utils.templating as templating
from pgsmo.objects.collation.collation import Collation
from pgsmo.objects.datatype.datatype import DataType
from pgsmo.objects.functions.function import Function
from pgsmo.objects.functions.trigger_function import TriggerFunction
from pgsmo.objects.sequence.sequence import Sequence
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
from pgsmo.objects.view.materialized_view import MaterializedView
from pgsmo.objects.extension.extension import Extension

from ostoolsservice.driver import ServerConnection    # noqa

class Database(NodeObject, ScriptableCreate, ScriptableDelete):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Database':
        """
        Creates a new Database object based on the results from a query to lookup databases
        :param server: Server that owns the database
        :param parent: Parent object of the database. Should always be None
        :param kwargs: Optional parameters for the database. Values that can be provided:
        Kwargs:
            oid int: Object ID of the database
            name str: Name of the database
            spcname str: Name of the tablespace for the database
            datallowconn bool: Whether or not the database can be connected to
            cancreate bool: Whether or not the database can be created by the current user
            owner int: Object ID of the user that owns the database
            datistemplate bool: Whether or not the database is a template database
            canconnect bool: Whether or not the database is accessbile to current user
        :return: Instance of the Database
        """
        db = cls(server, kwargs['name'])
        db._oid = kwargs['oid']
        db._tablespace = kwargs['spcname']
        db._allow_conn = kwargs['datallowconn']
        db._can_create = kwargs['cancreate']
        db._owner_oid = kwargs['owner']
        db._is_template = kwargs['datistemplate']
        db._can_connect = kwargs['canconnect']
        db._is_system = kwargs['is_system']
        db._datlastsysoid = kwargs['datlastsysoid']
        return db

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare the optional parameters
        self._tablespace: Optional[str] = None
        self._allow_conn: Optional[bool] = None
        self._is_template: Optional[bool] = None
        self._can_connect: Optional[bool] = None
        self._can_create: Optional[bool] = None
        self._owner_oid: Optional[int] = None
        self._connection: ServerConnection = None

        if server.maintenance_db_name == name:
            self._connection = server.connection

        # Declare the child items
        self._schemas = self._register_child_collection(Schema)
        self._tables: NodeCollection = self._register_child_collection(Table)
        self._views: NodeCollection = self._register_child_collection(View)
        self._collations: NodeCollection = self._register_child_collection(Collation)
        self._datatypes: NodeCollection = self._register_child_collection(DataType)
        self._functions: NodeCollection = self._register_child_collection(Function)
        self._sequences: NodeCollection = self._register_child_collection(Sequence)
        self._trigger_functions: NodeCollection = self._register_child_collection(TriggerFunction)
        self._extensions: NodeCollection = self._register_child_collection(Extension)
        self._materialized_views: NodeCollection = self._register_child_collection(MaterializedView)

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def allow_conn(self) -> bool:
        return self._allow_conn

    @property
    def connection(self) -> ServerConnection:
        if self._connection is not None:
            return self._connection
        else:
            # If we do not have a connection to the db, we create a new one
            connection: ServerConnection = self._server.db_connection_callback(self.name)
            if connection.database_name == self.name:
                self._connection = connection
                return self._connection
            else:
                raise ValueError('connection create for wrong database')

    @property
    def is_template(self) -> bool:
        return self._is_template

    @property
    def can_connect(self) -> bool:
        return self._can_connect

    @property
    def can_create(self) -> bool:
        return self._can_create

    @property
    def tablespace(self) -> str:
        return self._tablespace

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def spcoid(self) -> str:
        return self._full_properties.get("spcoid", "")

    @property
    def datowner(self) -> str:
        return self._full_properties.get("datowner", "")

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

    @property
    def default_tablespace(self):
        return self._full_properties.get("default_tablespace", "")

    @property
    def comments(self):
        return self._full_properties.get("comments", "")

    @property
    def tblacl(self):
        return self._full_properties.get("tblacl", "")

    @property
    def seqacl(self):
        return self._full_properties.get("seqacl", "")

    @property
    def funcacl(self):
        return self._full_properties.get("funcacl", "")

    @property
    def typeacl(self):
        return self._full_properties.get("typeacl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    # -CHILD OBJECTS #######################################################
    @property
    def schemas(self) -> NodeCollection[Schema]:
        return self._schemas

    @property
    def collations(self) -> NodeCollection:
        return self._collations

    @property
    def datatypes(self) -> NodeCollection:
        return self._datatypes

    @property
    def functions(self) -> NodeCollection:
        return self._functions

    @property
    def sequences(self) -> NodeCollection:
        return self._sequences

    @property
    def tables(self) -> NodeCollection:
        return self._tables

    @property
    def trigger_functions(self) -> NodeCollection:
        return self._trigger_functions

    @property
    def views(self) -> NodeCollection:
        return self._views

    @property
    def materialized_views(self) -> NodeCollection:
        return self._materialized_views

    @property
    def extensions(self) -> NodeCollection:
        return self._extensions

    @property
    def datlastsysoid(self) -> int:
        return self._datlastsysoid

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Return the data input for create query """
        return {"data": {
            "name": self.name,
            "datowner": self.datowner,
            "encoding": self.encoding,
            "template": self.template,
            "datcollate": self.datcollate,
            "datctype": self.datctype,
            "datconnlimit": self.datconnlimit,
            "spcname": self.spcname
        }}

    def _delete_query_data(self) -> dict:
        """ Return the data input for delete query """
        return {
            "did": self._oid,
            "datname": self._name
        }
