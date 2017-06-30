# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

import pgsmo.objects.column.column as col
import pgsmo.objects.node_object as node
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'view_templates')


class View:
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper, scid: int) -> List['View']:
        type_template_root = path.join(TEMPLATE_ROOT, conn.server_type)
        return node.get_nodes(conn, type_template_root, cls._from_node_query, scid=scid)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param conn: Connection used to execute the nodes query
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(kwargs['name'])
        view._conn = conn
        view._oid = kwargs['oid']

        return view

    def __init__(self, name: str):
        self._name: str = name

        # Declare optional parameters
        self._conn: Optional[utils.querying.ConnectionWrapper] = None
        self._oid: Optional[int] = None

        # Declare child items
        self._columns: Optional[List[col.Column]]

    # PROPERTIES ###########################################################
    @property
    def columns(self) -> Optional[List[col.Column]]:
        return self._columns

    @property
    def name(self) -> str:
        return self._name

    @property
    def oid(self) -> Optional[int]:
        return self._oid

    # METHODS ##############################################################
    def refresh(self) -> None:
        self._fetch_columns()

    # IMPLEMENTATION DETAILS ###############################################
    def _fetch_columns(self) -> None:
        self._columns = col.Column.get_columns_for_table(self._conn, self._oid)
