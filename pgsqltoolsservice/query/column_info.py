# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List
from psycopg2 import sql

from pgsqltoolsservice.query.contracts import DbColumn

def get_columns_info(description, connection) -> List[DbColumn]:

    if description is None:
        raise ValueError('Cursor description is not available')

    if connection is None:
        # if no connection is provided, just return basic column info constructed from the cursor description
        columns_info = []
        for index, column in enumerate(description):
            db_column = DbColumn.from_cursor_description(index, column)
            db_column._provider = "MySQL"
            columns_info.append(db_column)
        return columns_info

    # column_type_oids = [column_info[1] for column_info in description]

    # query_template = sql.SQL('SELECT {}, {} FROM {} WHERE {} IN ({})').format(
    #     sql.Identifier('oid'),
    #     sql.Identifier('typname'),
    #     sql.Identifier('pg_type'),
    #     sql.Identifier('oid'),
    #     sql.SQL(', ').join(sql.Placeholder() * len(column_type_oids))
    # )
    # columns_info = []

    # with connection.cursor() as type_cursor:
    #     type_cursor.execute(query_template, column_type_oids)
    #     rows = type_cursor.fetchall()
    #     rows_dict = dict(rows)

    #     for index, column in enumerate(description):
    #         db_column = DbColumn.from_cursor_description(index, column)
    #         db_column.data_type = rows_dict.get(column[1])
    #         columns_info.append(db_column)

    # return columns_info
