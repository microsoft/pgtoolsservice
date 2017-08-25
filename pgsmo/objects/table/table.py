# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.table_objects.column import Column
from pgsmo.objects.table_objects.constraints import (
    CheckConstraint,
    ExclusionConstraint,
    ForeignKeyConstraint,
    IndexConstraint
)
from pgsmo.objects.table_objects.index import Index
from pgsmo.objects.table_objects.rule import Rule
from pgsmo.objects.table_objects.trigger import Trigger
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Table(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

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
        table = cls(server, parent, kwargs['name'])
        table._oid = kwargs['oid']

        return table

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare child items
        self._check_constraints: NodeCollection[CheckConstraint] = self._register_child_collection(
            lambda: CheckConstraint.get_nodes_for_parent(self._server, self)
        )
        self._columns: NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._server, self)
        )
        self._exclusion_constraints: NodeCollection[ExclusionConstraint] = self._register_child_collection(
            lambda: ExclusionConstraint.get_nodes_for_parent(self._server, self)
        )
        self._foreign_key_constraints: NodeCollection[ForeignKeyConstraint] = self._register_child_collection(
            lambda: ForeignKeyConstraint.get_nodes_for_parent(self._server, self)
        )
        self._index_constraints: NodeCollection[IndexConstraint] = self._register_child_collection(
            lambda: IndexConstraint.get_nodes_for_parent(self._server, self)
        )
        self._indexes: NodeCollection[Index] = self._register_child_collection(
            lambda: Index.get_nodes_for_parent(self._server, self)
        )
        self._rules: NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._server, self)
        )
        self._triggers: NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._server, self)
        )

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.parent.oid,
            'did': self.parent.parent.oid,
            'datlastsysoid': 0  # temporary until implemented
        }
        return template_vars

    # -CHILD OBJECTS #######################################################
    @property
    def check_constraints(self) -> NodeCollection[CheckConstraint]:
        return self._check_constraints

    @property
    def columns(self) -> NodeCollection:
        return self._columns

    @property
    def exclusion_constraints(self) -> NodeCollection[ExclusionConstraint]:
        return self._exclusion_constraints

    @property
    def foreign_key_constraints(self) -> NodeCollection[ForeignKeyConstraint]:
        return self._foreign_key_constraints

    @property
    def index_constraints(self) -> NodeCollection[IndexConstraint]:
        return self._index_constraints

    @property
    def indexes(self) -> NodeCollection[Index]:
        return self._indexes

    @property
    def rules(self) -> NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> NodeCollection[Trigger]:
        return self._triggers

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def coll_inherits(self):
        return self._full_properties.get("coll_inherits", "")

    @property
    def typname(self):
        return self._full_properties.get("typname", "")

    @property
    def like_relation(self):
        return self._full_properties.get("like_relation", "")

    @property
    def primary_key(self):
        return self._full_properties.get("primary_key", "")

    @property
    def unique_constraint(self):
        return self._full_properties.get("unique_constraint", "")

    @property
    def foreign_key(self):
        return self._full_properties.get("foreign_key", "")

    @property
    def check_constraint(self):
        return self._full_properties.get("check_constraint", "")

    @property
    def exclude_constraint(self):
        return self._full_properties.get("exclude_constraint", "")

    @property
    def fillfactor(self):
        return self._full_properties.get("fillfactor", "")

    @property
    def spcname(self):
        return self._full_properties.get("spcname", "")

    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    @property
    def coll_inherits_added(self):
        return self._full_properties.get("coll_inherits_added", "")

    @property
    def coll_inherits_removed(self):
        return self._full_properties.get("coll_inherits_removed", "")

    @property
    def autovacuum_custom(self):
        return self._full_properties.get("autovacuum_custom", "")

    @property
    def autovacuum_enabled(self):
        return self._full_properties.get("autovacuum_enabled", "")

    @property
    def vacuum_table(self):
        return self._full_properties.get("vacuum_table", "")

    @property
    def toast_autovacuum(self):
        return self._full_properties.get("toast_autovacuum", "")

    @property
    def toast_autovacuum_enabled(self):
        return self._full_properties.get("toast_autovacuum_enabled", "")

    @property
    def vacuum_toast(self):
        return self._full_properties.get("vacuum_toast", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def hasoids(self):
        return self._full_properties.get("hasoids", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {"data": {
            "name": self.name,
            "coll_inherits": self.coll_inherits,
            "columns": self.columns,
            "typname": self.typname,
            "like_relation": self.like_relation,
            "primary_key": self.primary_key,
            "unique_constraint": self.unique_constraint,
            "foreign_key": self.foreign_key,
            "check_constraint": self.check_constraint,
            "exclude_constraint": self.exclude_constraint,
            "fillfactor": self.fillfactor,
            "spcname": self.spcname,
            "relowner": self.owner,
            "schema": self.parent.name
        }}

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {"data": {
            "name": self.name,
            "schema": self.parent.name,
            "relowner": self.owner,
            "coll_inherits_added": self.coll_inherits_added,
            "coll_inherits_removed": self.coll_inherits_removed,
            "relhasoids": self.hasoids,
            "spcname": self.spcname,
            "fillfactor": self.fillfactor,
            "autovacuum_custom": self.autovacuum_custom,
            "autovacuum_enabled": self.autovacuum_enabled,
            "vacuum_table.changed": self.vacuum_table.changed,
            "toast_autovacuum": self.toast_autovacuum,
            "toast_autovacuum_enabled": self.toast_autovacuum_enabled,
            "vacuum_toast.changed": self.vacuum_toast.changed,
            "description": self.description,
            "relacl": self.acl,
            "seclabels": self.seclabels
        }}
