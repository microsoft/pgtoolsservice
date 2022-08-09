# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from mysqlsmo.objects.column.column import Column
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect
from smo.common.node_object import NodeCollection, NodeObject
import smo.utils.templating as templating


class Table(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableSelect):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Table':
        """
        Creates a table instance from the results of a node query
        :param server: Server that owns the table
        :param parent: Parent object of the table. Should be a Schema
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the table
            name str: Name of the table
        :return: A table instance
        """
        table = cls(server, kwargs["name"], kwargs["dbname"])
        return table

    def __init__(self, server: 's.Server', name: str, dbname: str):
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableSelect.__init__(self, self._template_root(server), self._macro_root(), server.version)

        self._dbname = dbname
        self._server = server
        self._server_version = server.version
        self._columns: List[Column] = []

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "dbname": self._dbname,
            "tbl_name": self._name
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "dbname": self._dbname,
            "tbl_name": self._name
        }

    def _select_query_data(self) -> dict:
        """Provides data input for select script"""
        return {
            "dbname": self._dbname,
            "tbl_name": self._name
        }

    def create_script(self):
        """Generates a script that creates an object of the inheriting type"""
        data = self._create_query_data()
        template_root = self._template_root(self._server)
        sql = templating.render_template(
            templating.get_template_path(template_root, 'create.sql', self._server_version),
            macro_roots=self._macro_root(),
            **data
        )

        cols, rows = self._server.connection.execute_dict(sql)
        try:
            script = rows[0]["Create Table"]
        except Exception:
            script = rows[0]["Create View"]
        return script

    # PROPERTIES ###########################################################
    @property
    def columns(self) -> NodeCollection:
        return self._columns
