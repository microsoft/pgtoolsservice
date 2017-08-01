# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.table_objects import (
    Column,
    CheckConstraint,
    ExclusionConstraint,
    ForeignKeyConstraint,
    Index,
    IndexConstraint,
    Rule,
    Trigger
)
import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating
import pgsmo.utils.querying as querying


class Table(node.NodeObject):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Table':
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

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(Table, self).__init__(server, parent, name)

        # Declare child items
        self._check_constraints: node.NodeCollection[CheckConstraint] = self._register_child_collection(
            lambda: CheckConstraint.get_nodes_for_parent(self._server, self)
        )
        self._columns: node.NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._server, self)
        )
        self._exclusion_constraints: node.NodeCollection[ExclusionConstraint] = self._register_child_collection(
            lambda: ExclusionConstraint.get_nodes_for_parent(self._server, self)
        )
        self._foreign_key_constraints: node.NodeCollection[ForeignKeyConstraint] = self._register_child_collection(
            lambda: ForeignKeyConstraint.get_nodes_for_parent(self._server, self)
        )
        self._index_constraints: node.NodeCollection[IndexConstraint] = self._register_child_collection(
            lambda: IndexConstraint.get_nodes_for_parent(self._server, self)
        )
        self._indexes: node.NodeCollection[Index] = self._register_child_collection(
            lambda: Index.get_nodes_for_parent(self._server, self)
        )
        self._rules: node.NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._server, self)
        )
        self._triggers: node.NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._server, self)
        )

    # PROPERTIES ###########################################################
    # -CHILD OBJECTS #######################################################
    @property
    def check_constraints(self) -> node.NodeCollection[CheckConstraint]:
        return self._check_constraints

    @property
    def columns(self) -> node.NodeCollection:
        return self._columns

    @property
    def exclusion_constraints(self) -> node.NodeCollection[ExclusionConstraint]:
        return self._exclusion_constraints

    @property
    def foreign_key_constraints(self) -> node.NodeCollection[ForeignKeyConstraint]:
        return self._foreign_key_constraints

    @property
    def index_constraints(self) -> node.NodeCollection[IndexConstraint]:
        return self._index_constraints

    @property
    def indexes(self) -> node.NodeCollection[Index]:
        return self._indexes

    @property
    def rules(self) -> node.NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> node.NodeCollection[Trigger]:
        return self._triggers

    @property
    def schema(self):
        return self.parent

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
    def relacl(self):
        return self._full_properties.get("relacl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def relhasoids(self):
        return self._full_properties.get("relhasoids", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def get_template_vars(self):
        template_vars = {
            'tid': self.oid,
            'scid': self.parent.oid,
            'did': self.parent.parent.oid,
            'datlastsysoid': 0  # temporary until implemented
        }
        return template_vars

    # SCRIPTING METHODS ##############################################################
    def script(self, connection, action: str) -> str:
        """ Function to retrieve scripts for an operation """
        template_root = self._template_root(connection)
        if (action == "create"):
            data = self._create_query_data()
            query_file = "create.sql"
        elif (action == "delete"):
            data = self._delete_query_data()
            query_file = "delete.sql"
        elif (action == "update"):
            data = self._update_query_data()
            query_file = "update.sql"
        connection_version = querying.get_server_version(connection)
        template_path = templating.get_template_path(template_root, query_file, connection_version)
        script_template = templating.render_template(template_path, **data)
        return script_template

    # HELPER METHODS ####################################################################
    # QUERY DATA BUILDING METHODS #######################################################

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        data = {"data": {
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
            "relowner": self.relowner,
            "schema": self.parent_name
        }}
        return data

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        data = {
            "data": {
                "name": self.name,
                "schema": self.parent_name,
            }, "cascade": self.cascade
        }
        return data

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        data = {"data": {
            "name": self.name,
            "schema": self.parent_name,
            "relowner": self.relowner,
            "coll_inherits_added": self.coll_inherits_added,
            "coll_inherits_removed": self.coll_inherits_removed,
            "relhasoids": self.relhasoids,
            "spcname": self.spcname,
            "fillfactor": self.fillfactor,
            "autovacuum_custom": self.autovacuum_custom,
            "autovacuum_enabled": self.autovacuum_enabled,
            "vacuum_table.changed": self.vacuum_table.changed,
            "toast_autovacuum": self.toast_autovacuum,
            "toast_autovacuum_enabled": self.toast_autovacuum_enabled,
            "vacuum_toast.changed": self.vacuum_toast.changed,
            "description": self.description,
            "relacl": self.relacl,
            "seclabels": self.seclabels
        }}
        return data
