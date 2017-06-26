# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

import pgsmo.objects.column.column as col
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'view_templates')


class View:
    @staticmethod
    def get_views_for_schema(conn: utils.querying.ConnectionWrapper, scid: int) -> List['View']:
        type_template_root = path.join(TEMPLATE_ROOT, conn.server_type)
        sql = utils.templating.render_template(
            utils.templating.get_template_path(type_template_root, 'nodes.sql', conn.version),
            scid=scid
        )

        cols, rows = utils.querying.execute_dict(conn, sql)

        return [View._from_node_query(conn, row['oid'], row['name'], **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn, view_oid: int, view_name: str, fetch=True, **kwargs) -> 'View':
        view = cls(view_name)

        # Assign the optional properties
        view._conn = conn
        view._oid = view_oid

        # Fetch the children if requested
        if fetch:
            view.refresh()

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
