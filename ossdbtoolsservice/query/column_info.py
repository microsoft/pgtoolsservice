# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import psycopg
from psycopg import sql

from ossdbtoolsservice.query.contracts import DbColumn


def get_columns_info(cursor: psycopg.Cursor) -> list[DbColumn]:
    if cursor.description is None:
        raise ValueError("Cursor description is not available")

    if cursor.connection is None:
        # if no connection is provided, just return basic column info
        # constructed from the cursor description
        return [
            DbColumn.from_cursor_description(index, column)
            for index, column in enumerate(cursor.description)
        ]

    if hasattr(cursor, "provider"):
        columns_info = []
        for index, column in enumerate(cursor.description):
            db_column = DbColumn.from_cursor_description(index, column)
            columns_info.append(db_column)
        return columns_info

    else:
        column_type_oids = [column_info[1] for column_info in cursor.description]

        query_template = sql.SQL("SELECT {}, {} FROM {} WHERE {} IN ({})").format(
            sql.Identifier("oid"),
            sql.Identifier("typname"),
            sql.Identifier("pg_type"),
            sql.Identifier("oid"),
            sql.SQL(", ").join(sql.Placeholder() * len(column_type_oids)),
        )
        columns_info = []
        with cursor.connection.cursor() as type_cursor:
            type_cursor.execute(query_template, column_type_oids)
            rows = type_cursor.fetchall()
            rows_dict = dict(rows)

            for index, column in enumerate(cursor.description):
                db_column = DbColumn.from_cursor_description(index, column)
                db_column.data_type = rows_dict.get(column[1])
                columns_info.append(db_column)

        return columns_info
