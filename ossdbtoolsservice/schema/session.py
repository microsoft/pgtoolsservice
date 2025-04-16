# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from typing import Optional

import psycopg

from ossdbtoolsservice.connection import ServerConnection
from ossdbtoolsservice.hosting.context import RequestContext
from ossdbtoolsservice.schema.contracts import (
    GetSchemaModelResponseParams,
    SessionIdContainer,
)
from ossdbtoolsservice.schema.contracts.get_schema_model import (
    GET_SCHEMA_MODEL_COMPLETE,
    ColumnSchema,
    RelationshipSchema,
    TableSchema,
)
from ossdbtoolsservice.schema.contracts.session_control import CREATE_SESSION_COMPLETE


class SchemaEditorSession:
    id: str
    is_ready: bool
    _schema: GetSchemaModelResponseParams | None = None

    init_task: Optional[threading.Thread]
    get_schema_task: Optional[threading.Thread]

    def __init__(self, session_id: str) -> None:
        self.id = session_id
        self.is_ready = False
        self._schema = None

        self.init_task = None
        self.get_schema_task = None

    def initialize(self, request_context: RequestContext) -> None:
        self.init_task = threading.Thread(
            target=self._initialize_in_thread, args=(request_context,)
        )
        self.init_task.daemon = True
        self.init_task.start()
        return

    def _initialize_in_thread(self, request_context: RequestContext) -> None:
        response = SessionIdContainer(session_id=self.id)
        request_context.send_notification(CREATE_SESSION_COMPLETE, response)
        self.init_task = None
        return

    def get_schema_model(
        self, request_context: RequestContext, connection: ServerConnection
    ) -> None:
        # Check if we already have our schema cached
        if self._schema is not None:
            request_context.send_notification(
                GET_SCHEMA_MODEL_COMPLETE, self._schema)
            return

        # Check if retrieval is already in progress
        if self.get_schema_task is not None:
            request_context.send_error("Schema retrieval already in progress")
            return

        # Start a process to retrieve the schema
        self.get_schema_task = threading.Thread(
            target=self._get_schema_model_request_thread, args=(
                request_context, connection,)
        )
        self.get_schema_task.daemon = True
        self.get_schema_task.start()
        return

    def _get_schema_model_request_thread(
        self, request_context: RequestContext, connection: ServerConnection
    ) -> None:
        try:
            self._schema = self.get_schema_json(connection._conn)
            request_context.send_notification(
                GET_SCHEMA_MODEL_COMPLETE, self._schema)
        except Exception as e:
            request_context.send_error(f"Error fetching db context: {e}")
        return

    def get_schema_json(self, conn: psycopg.Connection) -> GetSchemaModelResponseParams:
        schema_resp = GetSchemaModelResponseParams(
            session_id=self.id, tables=[])

        # First, query for all user tables (exclude system schemas)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.oid AS id,
                    n.nspname AS schema,
                    c.relname AS name,
                    c.relrowsecurity AS rls_enabled,
                    c.relforcerowsecurity AS rls_forced,
                    CASE c.relreplident
                        WHEN 'd' THEN 'DEFAULT'
                        WHEN 'i' THEN 'INDEX'
                        WHEN 'f' THEN 'FULL'
                        WHEN 'n' THEN 'NOTHING'
                        ELSE c.relreplident
                    END AS replica_identity,
                    pg_total_relation_size(c.oid) AS bytes,
                    pg_size_pretty(pg_total_relation_size(c.oid)) AS size,
                    COALESCE(s.n_live_tup, 0) AS live_rows_estimate,
                    COALESCE(s.n_dead_tup, 0) AS dead_rows_estimate,
                    d.description AS comment,
                    -- Indicates if this table is a partitioned parent table
                    (p.partrelid IS NOT NULL) AS is_partitioned,
                    -- The parent table ID, if this is a child table
                    i.inhparent AS parent_id
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_stat_all_tables s ON s.relid = c.oid
                LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
                LEFT JOIN pg_partitioned_table p ON p.partrelid = c.oid
                LEFT JOIN pg_inherits i ON i.inhrelid = c.oid
                WHERE
                    -- Only include regular tables and partitioned parent tables
                    c.relkind IN ('r', 'p')
                    -- Exclude system schemas
                    AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, c.relname;
            """)
            tables = cur.fetchall()

        # Process each table
        for table_row in tables:
            (
                table_id, schema_name, table_name, rls_enabled, rls_forced,
                replica_identity, bytes_val, size_str, live_rows, dead_rows,
                comment, is_partitioned, parent_id
            ) = table_row

            table_dict = TableSchema(
                id=table_id,
                is_parent=is_partitioned,
                parent_id=parent_id,
                schema=schema_name,
                name=table_name,
                rls_enabled=rls_enabled,
                rls_forced=rls_forced,
                replica_identity=replica_identity,
                bytes=bytes_val,
                size=size_str,
                live_rows_estimate=live_rows,
                dead_rows_estimate=dead_rows,
                comment=comment,
                columns=[],
                primary_keys=[],
                relationships=[]
            )

            # Query columns for this table
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        column_name,
                        ordinal_position,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position;
                """, (schema_name, table_name))
                columns = cur.fetchall()

            if columns:
                table_dict.columns = []
                for col in columns:
                    (col_name, ordinal_position, data_type,
                     is_nullable, col_default, char_max_length) = col
                    col_obj = ColumnSchema(
                        name=col_name,
                        ordinal_position=ordinal_position,
                        data_type=data_type,
                        is_nullable=is_nullable == 'YES',
                        default=col_default,
                        character_maximum_length=char_max_length,
                    )
                    table_dict.columns.append(col_obj)

            # Query primary key columns for this table
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.attname AS column_name
                    FROM pg_index i
                    JOIN pg_attribute a
                        ON a.attrelid = i.indrelid
                        AND a.attnum = ANY(i.indkey)
                    JOIN pg_class c
                        ON c.oid = i.indrelid
                    JOIN pg_namespace n
                        ON n.oid = c.relnamespace
                    WHERE i.indisprimary
                    AND n.nspname = %s
                    AND c.relname = %s
                    ORDER BY a.attnum;
                """, (schema_name, table_name))
                pk_rows = cur.fetchall()
            table_dict.primary_keys = [row[0] for row in pk_rows]

            # Query foreign key relationships for this table
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        src_col.attname AS current_column,
                        tgt_ns.nspname AS foreign_schema,
                        tgt_tbl.relname AS foreign_table,
                        tgt_col.attname AS foreign_column
                    FROM
                        pg_constraint c
                        JOIN pg_class src_tbl
                            ON c.conrelid = src_tbl.oid
                        JOIN pg_namespace src_ns
                            ON src_tbl.relnamespace = src_ns.oid
                        JOIN pg_class tgt_tbl
                            ON c.confrelid = tgt_tbl.oid
                        JOIN pg_namespace tgt_ns
                            ON tgt_tbl.relnamespace = tgt_ns.oid
                        JOIN LATERAL unnest(c.conkey)
                            WITH ORDINALITY AS src(attnum, ord) ON TRUE
                        JOIN LATERAL unnest(c.confkey)
                            WITH ORDINALITY AS tgt(attnum, ord) ON src.ord = tgt.ord
                        JOIN pg_attribute src_col
                            ON src_col.attrelid = src_tbl.oid
                            AND src_col.attnum = src.attnum
                        JOIN pg_attribute tgt_col
                            ON tgt_col.attrelid = tgt_tbl.oid
                            AND tgt_col.attnum = tgt.attnum
                    WHERE
                        c.contype = 'f'
                        AND src_ns.nspname = %s
                        AND src_tbl.relname = %s
                    ORDER BY
                        src_col.attname, tgt_ns.nspname, tgt_tbl.relname, tgt_col.attname;
                """, (schema_name, table_name))
                fk_rows = cur.fetchall()
            table_dict.relationships = []
            for fk in fk_rows:
                col_name, foreign_schema, foreign_table, foreign_column = fk
                rel_obj = RelationshipSchema(
                    column=col_name,
                    foreign_table_schema=foreign_schema,
                    foreign_table_name=foreign_table,
                    foreign_column=foreign_column,
                )
                table_dict.relationships.append(rel_obj)

            schema_resp.tables.append(table_dict)

        return schema_resp

    def close_session(self) -> None:
        # TODO: Nothing to clean really?
        return
