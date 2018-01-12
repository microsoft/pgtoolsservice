# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect
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


class Table(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')
    GLOBAL_MACRO_ROOT = templating.get_template_root(__file__, '../global_macros')

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
        table._schema = kwargs['schema']
        table._scid = kwargs['schemaoid']
        table._is_system = kwargs['is_system']

        return table

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableSelect.__init__(self, self._template_root(server), self._macro_root(), server.version)
        self._schema: str = None
        self._scid: int = None
        # Declare child items
        self._check_constraints: NodeCollection[CheckConstraint] = self._register_child_collection(CheckConstraint)
        self._columns: NodeCollection[Column] = self._register_child_collection(Column)
        self._exclusion_constraints: NodeCollection[ExclusionConstraint] = self._register_child_collection(
            ExclusionConstraint
        )
        self._foreign_key_constraints: NodeCollection[ForeignKeyConstraint] = self._register_child_collection(
            ForeignKeyConstraint
        )
        self._index_constraints: NodeCollection[IndexConstraint] = self._register_child_collection(IndexConstraint)
        self._indexes: NodeCollection[Index] = self._register_child_collection(Index)
        self._rules: NodeCollection[Rule] = self._register_child_collection(Rule)
        self._triggers: NodeCollection[Trigger] = self._register_child_collection(Trigger)

    # PROPERTIES ###########################################################
    @property
    def schema(self):
        return self._schema

    @property
    def scid(self):
        return self._scid

    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.scid,
            'did': self.parent.oid,
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
    def spcoid(self):
        return self._full_properties.get("spcoid", "")

    @property
    def relacl_str(self):
        return self._full_properties.get("relacl_str", "")

    @property
    def relhasoids(self):
        return self._full_properties.get("relhasoids", "")

    @property
    def relhassubclass(self):
        return self._full_properties.get("relhassubclass", "")

    @property
    def reltuples(self):
        return self._full_properties.get("reltuples", "")

    @property
    def conname(self):
        return self._full_properties.get("conname", "")

    @property
    def conkey(self):
        return self._full_properties.get("conkey", "")

    @property
    def isrepl(self):
        return self._full_properties.get("isrepl", "")

    @property
    def triggercount(self):
        return self._full_properties.get("triggercount", "")

    @property
    def coll_inherits(self):
        return self._full_properties.get("coll_inherits", "")

    @property
    def inherited_tables_cnt(self):
        return self._full_properties.get("inherited_tables_cnt", "")

    @property
    def relpersistence(self):
        return self._full_properties.get("relpersistence", "")

    @property
    def autovacuum_vacuum_threshold(self):
        return self._full_properties.get("autovacuum_vacuum_threshold", "")

    @property
    def autovacuum_vacuum_scale_factor(self):
        return self._full_properties.get("autovacuum_vacuum_scale_factor", "")

    @property
    def autovacuum_analyze_threshold(self):
        return self._full_properties.get("autovacuum_analyze_threshold", "")

    @property
    def autovacuum_analyze_scale_factor(self):
        return self._full_properties.get("autovacuum_analyze_scale_factor", "")

    @property
    def autovacuum_vacuum_cost_delay(self):
        return self._full_properties.get("autovacuum_vacuum_cost_delay", "")

    @property
    def autovacuum_vacuum_cost_limit(self):
        return self._full_properties.get("autovacuum_vacuum_cost_limit", "")

    @property
    def autovacuum_freeze_min_age(self):
        return self._full_properties.get("autovacuum_freeze_min_age", "")

    @property
    def autovacuum_freeze_max_age(self):
        return self._full_properties.get("autovacuum_freeze_max_age", "")

    @property
    def autovacuum_freeze_table_age(self):
        return self._full_properties.get("autovacuum_freeze_table_age", "")

    @property
    def toast_autovacuum_vacuum_threshold(self):
        return self._full_properties.get("toast_autovacuum_vacuum_threshold", "")

    @property
    def toast_autovacuum_vacuum_scale_factor(self):
        return self._full_properties.get("toast_autovacuum_vacuum_scale_factor", "")

    @property
    def toast_autovacuum_analyze_threshold(self):
        return self._full_properties.get("toast_autovacuum_analyze_threshold", "")

    @property
    def toast_autovacuum_analyze_scale_factor(self):
        return self._full_properties.get("toast_autovacuum_analyze_scale_factor", "")

    @property
    def toast_autovacuum_vacuum_cost_delay(self):
        return self._full_properties.get("toast_autovacuum_vacuum_cost_delay", "")

    @property
    def toast_autovacuum_vacuum_cost_limit(self):
        return self._full_properties.get("toast_autovacuum_vacuum_cost_limit", "")

    @property
    def toast_autovacuum_freeze_min_age(self):
        return self._full_properties.get("toast_autovacuum_freeze_min_age", "")

    @property
    def toast_autovacuum_freeze_max_age(self):
        return self._full_properties.get("toast_autovacuum_freeze_max_age", "")

    @property
    def toast_autovacuum_freeze_table_age(self):
        return self._full_properties.get("toast_autovacuum_freeze_table_age", "")

    @property
    def table_vacuum_settings_str(self):
        return self._full_properties.get("table_vacuum_settings_str", "")

    @property
    def toast_table_vacuum_settings_str(self):
        return self._full_properties.get("toast_table_vacuum_settings_str", "")

    @property
    def reloptions(self):
        return self._full_properties.get("reloptions", "")

    @property
    def toast_reloptions(self):
        return self._full_properties.get("toast_reloptions", "")

    @property
    def reloftype(self):
        return self._full_properties.get("reloftype", "")

    @property
    def typname(self):
        return self._full_properties.get("typname", "")

    @property
    def hastoasttable(self):
        return self._full_properties.get("hastoasttable", "")

    @property
    def like_relation(self):
        return f'{self.schema}.{self.name}'

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
    def relowner(self):
        return self._full_properties.get("relowner", "")

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

    @property
    def is_sys_table(self):
        return self._full_properties.get("is_sys_table", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT, cls.GLOBAL_MACRO_ROOT]

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
            "primary_key": self.primary_key,
            "unique_constraint": self.unique_constraint,
            "foreign_key": self.foreign_key,
            "check_constraint": self.check_constraint,
            "exclude_constraint": self.exclude_constraint,
            "relpersistence": self.relpersistence,
            "relhasoids": self.relhasoids,
            "fillfactor": self.fillfactor,
            "autovacuum_custom": self.autovacuum_custom,
            "autovacuum_enabled": self.autovacuum_enabled,
            "toast_autovacuum": self.toast_autovacuum,
            "toast_autovacuum_enabled": self.toast_autovacuum_enabled,
            "autovacuum_analyze_scale_factor": self.autovacuum_analyze_scale_factor,
            "autovacuum_analyze_threshold": self.autovacuum_analyze_threshold,
            "autovacuum_freeze_max_age": self.autovacuum_freeze_max_age,
            "autovacuum_vacuum_cost_delay": self.autovacuum_vacuum_cost_delay,
            "autovacuum_vacuum_cost_limit": self.autovacuum_vacuum_cost_limit,
            "autovacuum_vacuum_scale_factor": self.autovacuum_vacuum_scale_factor,
            "autovacuum_vacuum_threshold": self.autovacuum_vacuum_threshold,
            "autovacuum_freeze_min_age": self.autovacuum_freeze_min_age,
            "autovacuum_freeze_table_age": self.autovacuum_freeze_table_age,
            "spcname": self.spcname,
            "relowner": self.relowner,
            "schema": self.schema
        }}

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {"data": {
            "name": self.name,
            "schema": self.schema,
            "relowner": self.relowner,
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

    def _select_query_data(self) -> dict:
        """Provides data input for select script"""
        return {"data": {
            "name": self.name,
            "schema": self.schema,
            "columns": self.columns
        }}
