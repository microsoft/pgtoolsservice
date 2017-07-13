# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

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
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Table(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, schema_id: int) -> List['Table']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, scid=schema_id)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Table':
        """
        Creates a table instance from the results of a node query
        :param conn: The connection used to execute the node query
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the table
            name str: Name of the table
        :return: A table instance
        """
        table = cls(conn, kwargs['name'])
        table._oid = kwargs['oid']

        return table

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(Table, self).__init__(conn, name)

        # Declare child items
        self._check_constraints: node.NodeCollection[CheckConstraint] = self._register_child_collection(
            lambda: CheckConstraint.get_nodes_for_parent(self._conn, self._oid)
        )
        self._columns: node.NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._conn, self._oid)
        )
        self._exclusion_constraints: node.NodeCollection[ExclusionConstraint] = self._register_child_collection(
            lambda: ExclusionConstraint.get_nodes_for_parent(self._conn, self._oid)
        )
        self._foreign_key_constraints: node.NodeCollection[ForeignKeyConstraint] = self._register_child_collection(
            lambda: ForeignKeyConstraint.get_nodes_for_parent(self._conn, self._oid)
        )
        self._index_constraints: node.NodeCollection[IndexConstraint] = self._register_child_collection(
            lambda: IndexConstraint.get_nodes_for_parent(self._conn, self._oid)
        )
        self._indexes: node.NodeCollection[Index] = self._register_child_collection(
            lambda: Index.get_nodes_for_parent(self._conn, self._oid)
        )
        self._rules: node.NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._conn, self._oid)
        )
        self._triggers: node.NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._conn, self._oid)
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
