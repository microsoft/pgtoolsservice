# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.objects.column.column as col
import pgsmo.objects.node_object as node
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Table:
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper, schema_id: int) -> List['Table']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, scid=schema_id)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Table':
        """
        Creates a table instance from the results of a node query
        :param conn: The connection used to execute the node query
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the table
            name str: Name of the table
        :return: A table instance
        """
        table = cls(kwargs['name'])
        table._conn = conn
        table._oid = kwargs['oid']

        return table

    def __init__(self, name: str):
        self._name: str = name

        # Declare the optional parameters
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
