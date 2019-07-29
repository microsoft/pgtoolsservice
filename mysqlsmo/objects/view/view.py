# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional
from smo.common.node_object import NodeCollection, NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect
from smo.utils import templating

class View(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'View':
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
        view = cls(server, kwargs["name"], kwargs["dbname"])
        return view

    def __init__(self, server: 's.Server', name: str, dbname: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableSelect.__init__(self, self._template_root(server), self._macro_root(), server.version)

        self._dbname = dbname

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "dbname": self._dbname,
            "view_name": self._name
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "dbname": self._dbname,
            "view_name": self._name
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {"data": {}}

    def _select_query_data(self) -> dict:
        """Provides data input for select script"""
        return {
            "dbname": self._dbname,
            "view_name": self._name
        }
