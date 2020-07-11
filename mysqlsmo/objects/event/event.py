# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from mysqlsmo.objects.server import MySQLServer
from typing import Optional
from smo.common.node_object import NodeCollection, NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from smo.utils import templating

class Event(NodeObject, ScriptableCreate, ScriptableDelete):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: MySQLServer, parent: None, **kwargs) -> 'Event':
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
        event = cls(server, kwargs["name"], kwargs["dbname"])
        return event

    def __init__(self, server: MySQLServer, name: str, dbname: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(self.server), self._macro_root(), self.server.version)
        ScriptableDelete.__init__(self, self._template_root(self.server), self._macro_root(), self.server.version)

        self._dbname = dbname

    @classmethod
    def _template_root(cls, server: MySQLServer) -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Return the data input for create query """
        return {
            "dbname": self._dbname,
            "event_name": self._name
        }

    def _delete_query_data(self) -> dict:
        """ Return the data input for delete query """
        return {
            "dbname": self._dbname,
            "event_name": self._name
        }