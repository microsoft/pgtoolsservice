# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.column.column import Column
import pgsmo.objects.node_object as node
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Table(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ServerConnection, schema_id: int) -> List['Table']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, scid=schema_id)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ServerConnection, **kwargs) -> 'Table':
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

    def __init__(self, conn: utils.querying.ServerConnection, name: str):
        super(Table, self).__init__(conn, name)

        # Declare child items
        self._columns: node.NodeCollection = node.NodeCollection(
            lambda: Column.get_nodes_for_parent(self._conn, self._oid)
        )

    # PROPERTIES ###########################################################
    # -CHILD OBJECTS #######################################################
    @property
    def columns(self) -> node.NodeCollection:
        return self._columns

    # METHODS ##############################################################
    def refresh(self) -> None:
        self._columns.reset()
