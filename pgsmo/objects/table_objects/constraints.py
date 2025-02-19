# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta

import smo.utils.templating as templating
from pgsmo.objects.server import server as s  # noqa
from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate


class Constraint(
    NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, metaclass=ABCMeta
):
    """Base class for constraints. Provides basic properties for all constraints"""

    @classmethod
    def _from_node_query(
        cls, server: "s.Server", parent: NodeObject, **kwargs
    ) -> "Constraint":
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
        constraint = cls(server, parent, kwargs["name"])
        constraint._oid = kwargs["oid"]
        if "convalidated" in kwargs:
            constraint._convalidated = kwargs["convalidated"]

        return constraint

    def __init__(self, server: "s.Server", parent: NodeObject, name: str):
        """
        Initializes a new instance of a constraint
        :param server: Connection the constraint belongs to
        :param parent: Parent object of the constraint. Should be Table
        :param name: Name of the constraint
        """

        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )
        ScriptableDelete.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )
        ScriptableUpdate.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )

        # Declare constraint-specific basic properties
        self._convalidated = None

    # PROPERTIES ###########################################################
    @property
    def convalidated(self):
        return self._convalidated

    @property
    def comment(self):
        return self._full_properties["comment"]


class CheckConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "constraint_check")

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def src(self):
        return self._full_properties["src"]

    @property
    def no_inherit(self):
        return self._full_properties["no_inherit"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
                "consrc": self.src,
                "comment": self.comment,
                "connoinherit": self.no_inherit,
                "convalidated": self.convalidated,
            },
            "conn": self.server.connection.connection,
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {
            "data": {
                "name": self.name,
                "nspname": self.parent.parent.name,
                "relname": self.parent.name,
            },
            "conn": self.server.connection.connection,
        }

    def _update_query_data(self) -> dict:
        """Function that returns data for update script"""
        return {
            "data": {
                "comment": self.comment,
                "name": self.name,
                "table": self.parent.name,
                "convalidated": self.convalidated,
            },
            "o_data": {
                "comment": "",
                "name": "",
                "nspname": "",
                "relname": "",
                "convalidated": "",
            },
            "conn": self.server.connection.connection,
        }


class ExclusionConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "constraint_exclusion")

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
    def deferrable(self):
        return self._full_properties["deferrable"]

    @property
    def deferred(self):
        return self._full_properties["deferred"]

    @property
    def constraint(self):
        return self._full_properties["constraint"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
                "amname": self.amname,
                "columns": self.columns,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "condeferrable": self.deferrable,
                "condeferred": self.deferred,
                "constraint": self.constraint,
                "comment": self.comment,
            },
            "conn": self.server.connection.connection,
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
            },
            "cascade": self.cascade,
            "conn": self.server.connection.connection,
        }

    def _update_query_data(self) -> dict:
        """Function that returns data for update script"""
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "spcname": self.spcname,
                "fillfactor": self.fillfactor,
                "comment": self.comment,
            },
            "o_data": {"name": "", "spcname": "", "fillfactor": "", "comment": ""},
            "conn": self.server.connection.connection,
        }


class ForeignKeyConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "constraint_fk")

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
    def fmatchtype(self):
        return self._full_properties["fmatchtype"]

    @property
    def fupdtype(self):
        return self._full_properties["fupdtype"]

    @property
    def fdeltype(self):
        return self._full_properties["fdeltype"]

    @property
    def deferrable(self):
        return self._full_properties["deferrable"]

    @property
    def deferred(self):
        return self._full_properties["deferred"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
                "columns": self.columns,
                "remote_schema": self.remote_schema,
                "remote_table": self.remote_table,
                "confmatchtype": self.fmatchtype,
                "confupdtype": self.fupdtype,
                "confdeltype": self.fdeltype,
                "condeferrable": self.deferrable,
                "condeferred": self.deferred,
                "convalidated": self.convalidated,
                "comment": self.comment,
            },
            "conn": self.server.connection.connection,
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
            },
            "cascade": self.cascade,
            "conn": self.server.connection.connection,
        }

    def _update_query_data(self) -> dict:
        """Function that returns data for update script"""
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "convalidated": self.convalidated,
                "comment": self.comment,
            },
            "o_data": {"name": "", "convalidated": "", "comment": ""},
            "conn": self.server.connection.connection,
        }


class IndexConstraint(Constraint):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "constraint_index")

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
    def deferrable(self):
        return self._full_properties["deferrable"]

    @property
    def deferred(self):
        return self._full_properties["deferred"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    # IMPLEMENTATION DETAILS ###############################################

    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
                "index": self.index,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "condeferrable": self.deferrable,
                "condeferred": self.deferred,
                "comment": self.comment,
            },
            "conn": self.server.connection.connection,
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {
            "data": {
                "schema": self.parent.schema,
                "table": self.parent.name,
                "name": self.name,
            },
            "cascade": self.cascade,
            "conn": self.server.connection.connection,
        }

    def _update_query_data(self) -> dict:
        """Function that returns data for update script"""
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "spcname": self.spcname,
                "fillfactor": self.fillfactor,
                "comment": self.comment,
            },
            "o_data": {"name": "", "spcname": "", "fillfactor": "", "comment": ""},
            "conn": self.server.connection.connection,
        }


class PrimaryKeyConstraint(IndexConstraint):
    @property
    def constraint_type(self):
        return "p"

    # TEMPLATING PROPERTIES ################################################
    @property
    def extended_vars(self) -> dict:
        return {
            "cid": self.oid,
            "tid": self.parent.oid,  # Table/view OID
            "did": self.parent.parent.oid,  # Database OID
            # Constraint type ("p" or "u" for primary or unique)
            "constraint_type": self.constraint_type,
        }


class UniqueKeyConstraint(IndexConstraint):
    @property
    def constraint_type(self):
        return "u"

    # TEMPLATING PROPERTIES ################################################
    @property
    def extended_vars(self) -> dict:
        return {
            "cid": self.oid,
            "tid": self.parent.oid,  # Table/view OID
            "did": self.parent.parent.oid,  # Database OID
            # Constraint type ("p" or "u" for primary or unique)
            "constraint_type": self.constraint_type,
        }
