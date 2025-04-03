# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading
from typing import Any, Dict, List, Optional

from ossdbtoolsservice.driver.types.driver import ServerConnection
from ossdbtoolsservice.hosting.context import RequestContext
from ossdbtoolsservice.schema.contracts.get_schema_model import ColumnSchema, RelationshipSchema, TableSchema
from ossdbtoolsservice.utils import constants
from pgsmo import Server
import psycopg

from ossdbtoolsservice.schema.contracts import (
        GetSchemaModelResponseParams,
        SessionIdContainer,
)

class SchemaEditorSession:
    owner_uri: str
    id: str
    is_ready: bool
    _server: Optional[Server]
    _schema: List[Dict[str, Any]] | None = None

    init_task: Optional[threading.Thread]
    get_schema_task: Optional[threading.Thread]

    def __init__(self, session_id: str, owner_uri: str) -> None:
        self.owner_uri = owner_uri
        self.id = session_id
        self.is_ready = False
        self._server = None
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
        request_context.send_response(response)
        self.init_task = None
        return


    def get_schema_model(self, request_context: RequestContext, connection: ServerConnection) -> None:
        # Check if we already have our schema cached
        if self._schema is not None:
            request_context.send_response(self._schema)
            return

        # Check if retrieval is already in progress
        if self.get_schema_task is not None:
            request_context.send_error("Schema retrieval already in progress")
            return

        # Start a process to retrieve the schema
        self.get_schema_task = threading.Thread(
            target=self._get_schema_model_request_thread, args=(request_context,connection,)
        )
        self.get_schema_task.daemon = True
        self.get_schema_task.start()
        return
    
    def _get_schema_model_request_thread(self, request_context: RequestContext, connection: ServerConnection):
        try:
            schema_resp = self.get_schema_json(connection._conn)
            request_context.send_response(schema_resp)
        except Exception as e:
            request_context.send_error(f"Error fetching db context: {e}")
        return
    
    def get_schema_json(self, conn: psycopg.Connection) -> Dict[str, Any]:
        schema_resp = GetSchemaModelResponseParams(tables=[])
        
        # First, query for all user tables (exclude system schemas)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.oid as id,
                    n.nspname as schema,
                    c.relname as name,
                    c.relrowsecurity as rls_enabled,
                    c.relforcerowsecurity as rls_forced,
                    CASE c.relreplident
                    WHEN 'd' THEN 'DEFAULT'
                    WHEN 'i' THEN 'INDEX'
                    WHEN 'f' THEN 'FULL'
                    WHEN 'n' THEN 'NOTHING'
                    ELSE c.relreplident
                    END as replica_identity,
                    pg_total_relation_size(c.oid) as bytes,
                    pg_size_pretty(pg_total_relation_size(c.oid)) as size,
                    COALESCE(s.n_live_tup, 0) as live_rows_estimate,
                    COALESCE(s.n_dead_tup, 0) as dead_rows_estimate,
                    d.description as comment
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                LEFT JOIN pg_stat_all_tables s ON s.relid = c.oid
                LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
                WHERE c.relkind = 'r'
                AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, c.relname;
            """)
            tables = cur.fetchall()
        
        # Process each table
        for table_row in tables:
            (
                table_id, schema_name, table_name, rls_enabled, rls_forced, 
                replica_identity, bytes_val, size_str, live_rows, dead_rows, comment
            ) = table_row
            
            table_dict = TableSchema(
                id=table_id,
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
                    col_name, ordinal_position, data_type, is_nullable, col_default, char_max_length = col
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
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                    ORDER BY kcu.ordinal_position;
                """, (schema_name, table_name))
                pk_rows = cur.fetchall()
            table_dict.primary_keys = [row[0] for row in pk_rows]
            
            # Query foreign key relationships for this table
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s;
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
    
    def close_session(self):
        # TODO
        return