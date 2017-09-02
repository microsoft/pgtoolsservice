# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Constraint(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    """Base class for constraints. Provides basic properties for all constraints"""
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_trigger')
    MACRO_ROOT = templating.get_template_root(__file__, '../table/macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Constraint':
        """
        Creates a constraint from the results of a node query for any constraint
        :param server: Server that owns the constraint
        :param parent: Parent object of the constraint. Should be Table/View
        :param kwargs: A row from a constraint nodes query
        Kwargs:
            name str: Name of the constraint
            oid int: Object ID of the constraint
            convalidated bool: ? TODO: Figure out what this value means
        :return: An instance of a constraint
        """
        constraint = cls(server, parent, kwargs['name'])
        constraint._oid = kwargs['oid']
        constraint._convalidated = kwargs['convalidated']

        return constraint

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes a new instance of a constraint
        :param server: Connection the constraint belongs to
        :param parent: Parent object of the constraint. Should be Table
        :param name: Name of the constraint
        """

        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare constraint-specific basic properties
        self._convalidated = None

    # PROPERTIES ###########################################################
    @property
    def convalidated(self):
        return self._convalidated

    @property
    def schema(self):
        return self._full_properties["schema"]

    @property
    def table(self):
        return self._full_properties["table"]

    @property
    def comment(self):
        return self._full_properties["comment"]


class CheckConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_check')
    MACRO_ROOT = templating.get_template_root(__file__, '../table/macros')

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def consrc(self):
        return self._full_properties["consrc"]

    @property
    def connoinherit(self):
        return self._full_properties["connoinherit"]

    @property
    def nspname(self):
        return self._full_properties["nspname"]

    @property
    def relname(self):
        return self._full_properties["relname"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name,
                "consrc": self.consrc,
                "comment": self.comment,
                "connoinherit": self.connoinherit,
                "convalidated": self.convalidated
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "nspname": self.nspname,
                "relname": self.relname
            }
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "comment": self.comment,
                "name": self.name,
                "table": self.table,
                "convalidated": self.convalidated
            },
            "o_data": {
                "comment": "",
                "name": "",
                "nspname": "",
                "relname": "",
                "convalidated": ""
            }
        }


class ExclusionConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_exclusion')
    MACRO_ROOT = templating.get_template_root(__file__, '../table/macros')

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def amname(self):
        return self._full_properties["amname"]

    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def fillfactor(self):
        return self._full_properties["fillfactor"]

    @property
    def spcname(self):
        return self._full_properties["spcname"]

    @property
    def condeferrable(self):
        return self._full_properties["condeferrable"]

    @property
    def condeferred(self):
        return self._full_properties["condeferred"]

    @property
    def constraint(self):
        return self._full_properties["constraint"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name,
                "amname": self.amname,
                "columns": self.columns,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "condeferrable": self.condeferrable,
                "condeferred": self.condeferred,
                "constraint": self.constraint,
                "comment": self.comment
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "table": self.table,
                "spcname": self.spcname,
                "fillfactor": self.fillfactor,
                "comment": self.comment
            },
            "o_data": {
                "name": "",
                "spcname": "",
                "fillfactor": "",
                "comment": ""
            }
        }


class ForeignKeyConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_fk')
    MACRO_ROOT = templating.get_template_root(__file__, '../table/macros')

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def remote_schema(self):
        return self._full_properties["remote_schema"]

    @property
    def remote_table(self):
        return self._full_properties["remote_table"]

    @property
    def confmatchtype(self):
        return self._full_properties["confmatchtype"]

    @property
    def confupdtype(self):
        return self._full_properties["confupdtype"]

    @property
    def confdeltype(self):
        return self._full_properties["confdeltype"]

    @property
    def condeferrable(self):
        return self._full_properties["condeferrable"]

    @property
    def condeferred(self):
        return self._full_properties["condeferred"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name,
                "columns": self.columns,
                "remote_schema": self.remote_schema,
                "remote_table": self.remote_table,
                "confmatchtype": self.confmatchtype,
                "confupdtype": self.confupdtype,
                "confdeltype": self.confdeltype,
                "condeferrable": self.condeferrable,
                "condeferred": self.condeferred,
                "convalidated": self.convalidated,
                "comment": self.comment
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "table": self.table,
                "convalidated": self.convalidated,
                "comment": self.comment
            },
            "o_data": {
                "name": "",
                "convalidated": "",
                "comment": ""
            }
        }


class IndexConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_constraint_index')
    MACRO_ROOT = templating.get_template_root(__file__, '../table/macros')

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def index(self):
        return self._full_properties["index"]

    @property
    def fillfactor(self):
        return self._full_properties["fillfactor"]

    @property
    def spcname(self):
        return self._full_properties["spcname"]

    @property
    def condeferrable(self):
        return self._full_properties["condeferrable"]

    @property
    def condeferred(self):
        return self._full_properties["condeferred"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name,
                "index": self.index,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "condeferrable": self.condeferrable,
                "condeferred": self.condeferred,
                "comment": self.comment
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "table": self.table,
                "spcname": self.spcname,
                "fillfactor": self.fillfactor,
                "comment": self.comment
            },
            "o_data": {
                "name": "",
                "spcname": "",
                "fillfactor": "",
                "comment": ""
            }
        }
