# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional               # noqa

from smo.common.node_object import NodeCollection, NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete
from smo.utils import templating
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
        db = cls(server, kwargs["Database"])
        return db

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(self.server), self._macro_root(), self.server.version)
        ScriptableDelete.__init__(self, self._template_root(self.server), self._macro_root(), self.server.version)


    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Return the data input for create query """
        pass

    def _delete_query_data(self) -> dict:
        """ Return the data input for delete query """
        return {
            "dbname": self._name
        }
