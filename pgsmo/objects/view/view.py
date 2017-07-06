# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List

from pgsmo.objects.table_objects.column.column import Column
import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating

TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')


class View(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, scid: int) -> List['View']:
        type_template_root = path.join(TEMPLATE_ROOT, conn.server_type)
        return node.get_nodes(conn, type_template_root, cls._from_node_query, scid=scid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param conn: Connection used to execute the nodes query
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(conn, kwargs['name'])
        view._oid = kwargs['oid']

        return view

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(View, self).__init__(conn, name)

        # Declare child items
        self._columns: node.NodeCollection = node.NodeCollection(
            lambda: Column.get_nodes_for_parent(self._conn, self.oid)
        )

    # PROPERTIES ###########################################################
    @property
    def columns(self) -> node.NodeCollection:
        return self._columns

    # METHODS ##############################################################
    def refresh(self) -> None:
        self._columns.reset()
