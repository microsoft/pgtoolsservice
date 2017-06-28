# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.objects.column.column as col
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Table:
    @staticmethod
    def get_tables_for_schema(conn: utils.querying.ServerConnection, schema_id: int) -> List['Table']:
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version),
            scid=schema_id
        )

        cols, rows = conn.execute_dict(sql)

        return [Table._from_node_query(conn, row['oid'], row['name'], **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn, table_oid: int, table_name: str, fetch=True, **kwargs) -> 'Table':
        table = cls(table_name)

        # Assign the mandatory properties
        table._oid = table_oid
        table._conn = conn

        # If fetch was requested, do complete refresh
        if fetch:
            table.refresh()

        return table

    def __init__(self, name: str):
        self._name: str = name

        # Declare the optional parameters
        self._conn: Optional[utils.querying.ServerConnection] = None
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
