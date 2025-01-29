from psycopg import sql, Connection


def fetch_schema(connection: Connection, schema_name: str = "public") -> str:
    """Fetch the schema creation script for the database."""
    with connection.cursor() as cur:
        schema_creation_script = []

        # Fetch extensions for the database
        cur.execute(sql.SQL("SELECT extname FROM pg_extension;"))
        extensions = cur.fetchall()
        schema_creation_script.extend(
            f"CREATE EXTENSION IF NOT EXISTS {ext[0]};" for ext in extensions
        )
        schema_creation_script.append(f"CREATE SCHEMA {schema_name};")

        # Fetch tables for the schema
        cur.execute(
            sql.SQL("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = {};
            """).format(sql.Literal(schema_name))
        )
        tables = cur.fetchall()

        for table in tables:
            table_name = table[0]
            # Get CREATE TABLE statement with constraints
            cur.execute(
                sql.SQL("""
                    SELECT 'CREATE TABLE ' || table_schema || '.' || table_name || ' (' ||
                    string_agg(column_name || ' ' || 
                                CASE 
                                    WHEN data_type = 'USER-DEFINED' THEN 
                                        (SELECT pg_catalog.format_type(atttypid, atttypmod) 
                                         FROM pg_attribute 
                                         WHERE attrelid = (SELECT oid FROM pg_class WHERE relname = table_name) 
                                         AND attname = column_name)
                                    ELSE data_type 
                                END || 
                                COALESCE('(' || character_maximum_length || ')', '') || 
                                COALESCE(' ' || column_default, '') || 
                                CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END, ', ') || 
                    COALESCE(', ' || string_agg(constraint_name || ' ' || constraint_type, ', '), '') || ');'
                    FROM (
                        SELECT c.table_schema, c.table_name, c.column_name, c.data_type, c.character_maximum_length, c.column_default, c.is_nullable,
                               tc.constraint_name, tc.constraint_type
                        FROM information_schema.columns c
                        LEFT JOIN (
                            SELECT tc.table_schema, tc.table_name, kcu.column_name, tc.constraint_name, tc.constraint_type
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                            AND tc.table_name = kcu.table_name
                        ) tc
                        ON c.table_schema = tc.table_schema
                        AND c.table_name = tc.table_name
                        AND c.column_name = tc.column_name
                        WHERE c.table_schema = {} AND c.table_name = {}
                    ) sub
                    GROUP BY table_schema, table_name;
                """).format(sql.Literal(schema_name), sql.Literal(table_name))
            )
            create_table_stmt = cur.fetchone()
            if create_table_stmt:
                schema_creation_script.append(create_table_stmt[0])

        # Fetch indexes for the schema
        cur.execute(
            sql.SQL("""
                SELECT indexdef
                FROM pg_indexes
                WHERE schemaname = {};
            """).format(sql.Literal(schema_name))
        )
        indexes = cur.fetchall()
        schema_creation_script.extend(idx[0] for idx in indexes)

        # Fetch sequences for the schema
        cur.execute(
            sql.SQL("""
                SELECT sequence_schema, sequence_name, data_type, start_value, increment, maximum_value, minimum_value, cycle_option
                FROM information_schema.sequences
                WHERE sequence_schema = {};
            """).format(sql.Literal(schema_name))
        )
        sequences = cur.fetchall()
        for seq in sequences:
            schema_creation_script.append(
                f"CREATE SEQUENCE {seq[0]}.{seq[1]} "
                f"AS {seq[2]} "
                f"START WITH {seq[3]} "
                f"INCREMENT BY {seq[4]} "
                f"MINVALUE {seq[6]} "
                f"MAXVALUE {seq[5]} "
                f"{'CYCLE' if seq[7] == 'YES' else 'NO CYCLE'};"
            )

        # Fetch views for the schema
        cur.execute(
            sql.SQL("""
                SELECT table_name, view_definition
                FROM information_schema.views
                WHERE table_schema = {};
            """).format(sql.Literal(schema_name))
        )
        views = cur.fetchall()
        schema_creation_script.extend(
            f"CREATE VIEW {schema_name}.{view[0]} AS {view[1]};" for view in views
        )

        # Fetch functions and procedures for the schema
        cur.execute(
            sql.SQL("""
                SELECT routine_name, routine_definition
                FROM information_schema.routines
                WHERE routine_schema = {};
            """).format(sql.Literal(schema_name))
        )
        routines = cur.fetchall()
        schema_creation_script.extend(
            f"CREATE FUNCTION {schema_name}.{routine[0]} AS $$ {routine[1]} $$ LANGUAGE plpgsql;"
            for routine in routines
        )

        # Fetch triggers for the schema
        cur.execute(
            sql.SQL("""
                SELECT tgname, pg_get_triggerdef(t.oid)
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = {};
            """).format(sql.Literal(schema_name))
        )
        triggers = cur.fetchall()
        schema_creation_script.extend(
            f"CREATE TRIGGER {trigger[0]} {trigger[1]};" for trigger in triggers
        )

        return "\n".join(schema_creation_script)


def execute_readonly_query(connection: Connection, query: str) -> str:
    """Execute a read-only query against the database."""
    with connection.cursor() as cur:
        cur.execute("BEGIN TRANSACTION READ ONLY;")
        cur.execute(sql.SQL(query))
        result = cur.fetchall()
        connection.rollback()
        return str(result)


def execute_statement(connection: Connection, statement: str) -> str:
    """Execute a statement against the database."""
    with connection.cursor() as cur:
        cur.execute(sql.SQL(statement))
        return "Statement executed successfully."
