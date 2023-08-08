# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from psycopg import (ClientCursor, OperationalError)
from textwrap import (dedent)
import re

def _pretty_type(dt):
    dt = re.sub('timestamp with time zone', 'timestamptz', dt)
    dt = re.sub('timestamp without time zone', 'timestamp', dt)
    dt = re.sub('character varying', 'varchar', dt)
    dt = re.sub('double precision', 'double', dt)
    dt = re.sub('boolean', 'bool', dt)
    dt = re.sub('integer', 'int', dt)
    return dt.lower()

def _pretty_constraint(constraint):
    return (constraint.rsplit(')', 1)[0] + ")").lower()

def _pretty_index(indexdef):
    return indexdef.split(' USING ')[1].lower()

class SchemaMetadata:
    """Describe the schema to an LLM"""

    def __init__(self, cur: ClientCursor, schema: str = "public"):
        self.cur = cur
        self.schema = schema

    def describe(self) -> str:
        t = self.describe_tables()
        c = self.describe_constraints()
        i = self.describe_indexes()
        return f"## PostgreSQL database schema\n{t}{c}{i}"

    def describe_tables(self) -> str:
        results = dedent("""
        ## Tables and columns in the schema, in the form:
        table_name
        \tcolumn_name/type
        \tcolumn_name/type
        """)

        self.cur.execute(
        f"""
        SELECT
            t.table_name,
            column_name,
            data_type
        FROM
            information_schema.tables AS t
            INNER JOIN information_schema.columns AS c
                ON t.table_name = c.table_name
        WHERE
            t.table_schema = '{self.schema}'
        AND t.table_name NOT LIKE '%\_p%' --exclude partitions
        AND t.table_name NOT LIKE 'pg\_%' --exclude system tables
        ORDER BY
            t.table_name,
            c.ordinal_position;
        """
        )
        tables = self.cur.fetchall()

        cur_table = None
        for table, column, dt in tables:
            if table != cur_table:
                cur_table = table
                results += table
            results += f"\t{column}/{_pretty_type(dt)}"

        return results

    def describe_constraints(self) -> str:
        results = dedent("""
        ## Table constraints, in the form:
        table_name
        \tconstraint_def
        \tconstraint_def
        """)

        self.cur.execute(
        f"""
        SELECT
            t.relname AS table_name,
            pg_get_constraintdef(c.oid) AS definition
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE c.contype IN ('p', 'u', 'f')
            AND t.relname IN (
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{self.schema}'
                AND tablename NOT LIKE '%\_p%' --exclude partitions
                AND tablename NOT LIKE 'pg\_%' --exclude system tables
            )
        ORDER BY 1, 2;
        """
        )
        tables = self.cur.fetchall()

        cur_table = None
        for table, constraint in tables:
            if table != cur_table:
                cur_table = table
                results += table
            results += "\t" + _pretty_constraint(constraint)

        return results

    def describe_indexes(self) -> str:
        results = dedent("""
        ## Table indexes, in the form:
        table_name
        \ttype (column_name, column_name)
        \ttype (column_name, column_name)
        """)

        self.cur.execute(
        f"""
        SELECT tablename, indexdef
        FROM pg_indexes
        WHERE schemaname = '{self.schema}'
        AND tablename NOT LIKE '%\_p%' --exclude partitions
        AND tablename NOT LIKE 'pg\_%' --exclude system tables
        ORDER BY 1, 2;
        """
        )
        tables = self.cur.fetchall()
        cur_table = None
        for table, indx in tables:
            if table != cur_table:
                cur_table = table
                results += table
            results += "\t" + _pretty_index(indx)

        return results