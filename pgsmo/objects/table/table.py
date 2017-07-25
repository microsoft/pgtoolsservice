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

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
