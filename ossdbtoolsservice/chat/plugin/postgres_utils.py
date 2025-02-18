from psycopg import Connection, sql


def fetch_schemas_and_tables(connection: Connection) -> str:
    """Fetch all user schemas and their tables."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT
                table_schema,
                table_name
            FROM
                information_schema.tables
            WHERE
                table_type = 'BASE TABLE'
                AND table_schema NOT IN ('pg_catalog', 'information_schema')
                AND table_schema NOT LIKE 'pg_%'
            ORDER BY
                table_schema,
                table_name;
            """
        )
        schemas_and_tables = cur.fetchall()
        return str(schemas_and_tables)


def execute_readonly_query(
    connection: Connection, query: str, max_result_chars: int = 7000
) -> str:
    """Execute a read-only query against the database."""
    with connection.cursor() as cur:
        cur.execute("BEGIN TRANSACTION READ ONLY;")
        try:
            cur.execute(wrap_sql(query))
            result = cur.fetchall()
            result_str = str(result)
            # Format as CSV
            if result:
                if cur.description:
                    headers = [desc.name for desc in cur.description]
                    result_str = ",".join(headers) + "\n"
                    result_str += "\n".join(
                        ",".join(str(cell) for cell in row) for row in result
                    )
                else:
                    result_str = str(result)

            # Estimate the number of tokens in the result
            if len(result_str) > max_result_chars:
                return (
                    f"Result has {len(result)} rows, and is too large to return. "
                    "Run the query in an editor to see the full result."
                )
            return result_str
        finally:
            connection.rollback()


def execute_statement(connection: Connection, statement: str) -> str:
    """Execute a statement against the database."""
    with connection.cursor() as cur:
        cur.execute(wrap_sql(statement))
        return "Statement executed successfully."


def wrap_sql(statement: str) -> sql.SQL:
    """Wrap a SQL statement in a transaction."""
    return sql.SQL(statement)  # type:ignore


def fetch_schema_v1(connection: Connection, schema_name: str = "public") -> str:
    """Fetch the full schema creation script for the database."""
    with connection.cursor() as cur:
        schema_creation_script = []

        # Get postgres version
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            schema_creation_script.append(f"-- PostgreSQL version: {version[0]}")

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
                            WHERE attrelid = (
                            SELECT oid FROM pg_class 
                            WHERE relname = table_name
                            )
                            AND attname = column_name)
                    ELSE data_type
                END ||
                COALESCE('(' || character_maximum_length || ')', '') ||
                COALESCE(' ' || column_default, '') ||
                CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END, ', ') ||
    COALESCE(', ' || string_agg(constraint_name || ' ' || constraint_type, ', '), '') || ');'
    FROM (
        SELECT c.table_schema, 
                c.table_name, 
                c.column_name, 
                c.data_type, 
                c.character_maximum_length, 
                c.column_default, 
                c.is_nullable,
                tc.constraint_name, 
                tc.constraint_type
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT 
                tc.table_schema, 
                tc.table_name, 
                kcu.column_name, 
                tc.constraint_name, 
                tc.constraint_type
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
                SELECT 
                        sequence_schema, 
                        sequence_name, 
                        data_type, 
                        start_value, 
                        increment, 
                        maximum_value, 
                        minimum_value, 
                        cycle_option
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
            f"CREATE FUNCTION {schema_name}.{routine[0]} "
            f"AS $$ {routine[1]} $$ LANGUAGE plpgsql;"
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


def fetch_schema_v2(connection: Connection) -> str:
    """Fetch the schema and table creation script for each schema in the database."""
    with connection.cursor() as cur:
        schema_creation_script = []

        # Get postgres version
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            schema_creation_script.append(f"-- PostgreSQL version: {version[0]}")

        # Fetch extensions for the database
        cur.execute(sql.SQL("SELECT extname FROM pg_extension;"))
        extensions = cur.fetchall()
        schema_creation_script.extend(
            f"CREATE EXTENSION IF NOT EXISTS {ext[0]};" for ext in extensions
        )

        # Fetch all schema names
        cur.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            AND schema_name NOT LIKE 'pg_%';
            """
        )
        schemas = cur.fetchall()

        for schema in schemas:
            schema_name = schema[0]
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
    SELECT c.table_schema, c.table_name, c.column_name, c.data_type, 
            c.character_maximum_length, c.column_default, c.is_nullable,
            tc.constraint_name, tc.constraint_type
    FROM information_schema.columns c
    LEFT JOIN (
        SELECT tc.table_schema, tc.table_name, kcu.column_name, tc.constraint_name, 
                tc.constraint_type
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

        return "\n".join(schema_creation_script)


def fetch_schema_v3(connection: Connection) -> str:
    """
    Fetch the complete schema creation script for each non-system schema,
    including partitioned tables and their partitions (attached via ALTER TABLE).
    """
    with connection.cursor() as cur:
        schema_creation_script = []

        # PostgreSQL version as a comment.
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            schema_creation_script.append(f"-- PostgreSQL version: {version[0]}")

        # Create extensions.
        cur.execute("SELECT extname FROM pg_extension;")
        for (extname,) in cur.fetchall():
            schema_creation_script.append(f"CREATE EXTENSION IF NOT EXISTS {extname};")

        # Get non-system schemas.
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
              AND schema_name NOT LIKE 'pg_%';
        """)
        schemas = cur.fetchall()

        for (schema_name,) in schemas:
            schema_creation_script.append(f"CREATE SCHEMA {schema_name};")

            # Query objects in the schema.
            # Note: We exclude tables that are partitions (i.e. that appear in pg_inherits)
            cur.execute(
                sql.SQL("""
                SELECT c.relname, c.relkind, c.oid
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND c.relkind IN ('r', 'p', 'f', 'v', 'm')
                  AND (c.relkind NOT IN ('r', 'f') OR c.oid NOT IN (
                        SELECT inhrelid FROM pg_inherits))
                ORDER BY c.relname;
            """),
                [schema_name],
            )
            for obj_name, relkind, _oid in cur.fetchall():
                full_name = f"{schema_name}.{obj_name}"

                if relkind in ("r", "p", "f"):
                    # Build column definitions from pg_attribute.
                    cur.execute(
                        sql.SQL("""
                        SELECT a.attname,
                               pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                               a.attnotnull,
                               pg_get_expr(ad.adbin, ad.adrelid) AS default_value
                        FROM pg_attribute a
                        LEFT JOIN pg_attrdef ad
                          ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
                        WHERE a.attrelid = %s::regclass
                          AND a.attnum > 0
                          AND NOT a.attisdropped
                        ORDER BY a.attnum;
                    """),
                        [full_name],
                    )
                    columns = cur.fetchall()
                    col_defs = []
                    for col_name, data_type, attnotnull, default_value in columns:
                        col_def = f"{col_name} {data_type}"
                        if default_value is not None:
                            col_def += f" DEFAULT {default_value}"
                        if attnotnull:
                            col_def += " NOT NULL"
                        col_defs.append(col_def)

                    # Add constraints via pg_constraint.
                    cur.execute(
                        sql.SQL("""
                        SELECT conname, pg_get_constraintdef(oid, true)
                        FROM pg_constraint
                        WHERE conrelid = %s::regclass
                        ORDER BY contype;
                    """),
                        [full_name],
                    )
                    for conname, condef in cur.fetchall():
                        col_defs.append(f"CONSTRAINT {conname} {condef}")

                    stmt = (
                        f"CREATE TABLE {full_name} (\n    " + ",\n    ".join(col_defs) + "\n)"
                    )

                    # If the table is partitioned, append the PARTITION BY clause.
                    if relkind == "p":
                        cur.execute(
                            sql.SQL("SELECT pg_get_partkeydef(%s::regclass);"),
                            [full_name],
                        )
                        partdef = cur.fetchone()[0]
                        if partdef:
                            stmt += f" PARTITION BY {partdef}"

                    # If the table is a foreign table, adjust the DDL accordingly.
                    if relkind == "f":
                        cur.execute(
                            sql.SQL("""
                            SELECT fs.srvname,
                                   array_to_string(ft.ftoptions, ', ')
                            FROM pg_foreign_table ft
                            JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                            WHERE ft.ftrelid = %s::regclass;
                        """),
                            [full_name],
                        )
                        foreign_info = cur.fetchone()
                        if foreign_info:
                            srvname, options = foreign_info
                            stmt = stmt.replace("CREATE TABLE", "CREATE FOREIGN TABLE", 1)
                            stmt += f" SERVER {srvname}"
                            if options:
                                stmt += f" OPTIONS ({options})"
                    stmt += ";"
                    schema_creation_script.append(stmt)

                    # *** NEW: If the table is partitioned, fetch and attach its partitions.
                    if relkind == "p":
                        cur.execute(
                            sql.SQL("""
                            SELECT child.relname,
                                   pg_get_expr(child.relpartbound, child.oid) AS part_bound
                            FROM pg_inherits i
                            JOIN pg_class child ON i.inhrelid = child.oid
                            WHERE i.inhparent = %s::regclass;
                        """),
                            [full_name],
                        )
                        partitions = cur.fetchall()
                        for part_name, part_bound in partitions:
                            child_full_name = f"{schema_name}.{part_name}"
                            alter_stmt = (
                                f"ALTER TABLE {full_name} ATTACH PARTITION {child_full_name}"
                            )
                            if part_bound:
                                # pg_get_expr returns a string like 
                                # "FOR VALUES FROM (...) TO (...)"
                                alter_stmt += f" {part_bound}"
                            alter_stmt += ";"
                            schema_creation_script.append(alter_stmt)

                elif relkind == "v":
                    # For views, use pg_get_viewdef.
                    cur.execute(
                        sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"),
                        [full_name],
                    )
                    viewdef = cur.fetchone()[0]
                    stmt = f"CREATE OR REPLACE VIEW {full_name} AS\n{viewdef};"
                    schema_creation_script.append(stmt)

                elif relkind == "m":
                    # For materialized views.
                    cur.execute(
                        sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"),
                        [full_name],
                    )
                    viewdef = cur.fetchone()[0]
                    stmt = f"CREATE MATERIALIZED VIEW {full_name} AS\n{viewdef} WITH DATA;"
                    schema_creation_script.append(stmt)

        return "\n".join(schema_creation_script)


def fetch_schema_v4(connection: Connection) -> str:
    """
    Fetch a complete schema creation script for each non-system schema in the database,
    including tables, partitioned tables (with ALTER TABLE ... ATTACH PARTITION),
    foreign tables, views, materialized views, sequences, indexes, triggers, and functions.
    Objects contributed by installed extensions 
    (those with pg_depend.deptype = 'e') are excluded.
    """
    with connection.cursor() as cur:
        schema_creation_script = []

        # PostgreSQL version (as a comment)
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            schema_creation_script.append(f"-- PostgreSQL version: {version[0]}")

        # Create extensions (we still create these, 
        # but later exclude their contributed objects)
        cur.execute("SELECT extname FROM pg_extension;")
        for (extname,) in cur.fetchall():
            schema_creation_script.append(f"CREATE EXTENSION IF NOT EXISTS {extname};")

        # Get all non-system schemas.
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
              AND schema_name NOT LIKE 'pg_%';
        """)
        schemas = cur.fetchall()

        for (schema_name,) in schemas:
            schema_creation_script.append(f"CREATE SCHEMA {schema_name};")

            # -- Process tables (regular, partitioned, foreign), 
            # views, and materialized views.
            cur.execute(
                sql.SQL("""
    SELECT c.relname, c.relkind, c.oid
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname = %s
        AND c.relkind IN ('r', 'p', 'f', 'v', 'm')
        -- For regular and foreign tables, exclude those that are partitions.
        AND (c.relkind NOT IN ('r', 'f') OR c.oid NOT IN (SELECT inhrelid FROM pg_inherits))
    ORDER BY c.relname;
            """),
                [schema_name],
            )
            objects = cur.fetchall()

            for obj_name, relkind, _oid in objects:
                full_name = f"{schema_name}.{obj_name}"
                if relkind in ("r", "p", "f"):
                    # Build CREATE TABLE (or CREATE FOREIGN TABLE) DDL
                    cur.execute(
                        sql.SQL("""
                        SELECT a.attname,
                               pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
                               a.attnotnull,
                               pg_get_expr(ad.adbin, ad.adrelid) AS default_value
                        FROM pg_attribute a
                        LEFT JOIN pg_attrdef ad
                          ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
                        WHERE a.attrelid = %s::regclass
                          AND a.attnum > 0
                          AND NOT a.attisdropped
                        ORDER BY a.attnum;
                    """),
                        [full_name],
                    )
                    columns = cur.fetchall()
                    col_defs = []
                    for col_name, data_type, attnotnull, default_value in columns:
                        col_def = f"{col_name} {data_type}"
                        if default_value is not None:
                            col_def += f" DEFAULT {default_value}"
                        if attnotnull:
                            col_def += " NOT NULL"
                        col_defs.append(col_def)

                    # Append constraints 
                    # (ensuring multi‑column constraints are output only once)
                    cur.execute(
                        sql.SQL("""
                        SELECT conname, pg_get_constraintdef(oid, true)
                        FROM pg_constraint
                        WHERE conrelid = %s::regclass
                        ORDER BY contype;
                    """),
                        [full_name],
                    )
                    for conname, condef in cur.fetchall():
                        col_defs.append(f"CONSTRAINT {conname} {condef}")

                    stmt = (
                        f"CREATE TABLE {full_name} (\n    " + ",\n    ".join(col_defs) + "\n)"
                    )

                    # If partitioned, add the PARTITION BY clause.
                    if relkind == "p":
                        cur.execute(
                            sql.SQL("SELECT pg_get_partkeydef(%s::regclass);"),
                            [full_name],
                        )
                        partdef = cur.fetchone()[0]
                        if partdef:
                            stmt += f" PARTITION BY {partdef}"

                    # If a foreign table, adjust the DDL.
                    if relkind == "f":
                        cur.execute(
                            sql.SQL("""
                            SELECT fs.srvname,
                                   array_to_string(ft.ftoptions, ', ')
                            FROM pg_foreign_table ft
                            JOIN pg_foreign_server fs ON ft.ftserver = fs.oid
                            WHERE ft.ftrelid = %s::regclass;
                        """),
                            [full_name],
                        )
                        foreign_info = cur.fetchone()
                        if foreign_info:
                            srvname, options = foreign_info
                            stmt = stmt.replace("CREATE TABLE", "CREATE FOREIGN TABLE", 1)
                            stmt += f" SERVER {srvname}"
                            if options:
                                stmt += f" OPTIONS ({options})"
                    stmt += ";"
                    schema_creation_script.append(stmt)

                    # Add triggers for this table.
                    cur.execute(
                        sql.SQL("""
                        SELECT tgname, pg_get_triggerdef(t.oid, true)
                        FROM pg_trigger t
                        WHERE t.tgrelid = %s::regclass
                          AND NOT t.tgisinternal
                          AND NOT EXISTS (
                              SELECT 1 FROM pg_depend d
                              WHERE d.objid = t.oid AND d.deptype = 'e'
                          );
                    """),
                        [full_name],
                    )
                    for _tgname, tgdef in cur.fetchall():
                        # pg_get_triggerdef returns the trigger definition 
                        # (without a trailing semicolon)
                        schema_creation_script.append(tgdef + ";")

                    # For partitioned tables, attach child partitions.
                    if relkind == "p":
                        cur.execute(
                            sql.SQL("""
                            SELECT child.relname,
                                   pg_get_expr(child.relpartbound, child.oid) AS part_bound
                            FROM pg_inherits i
                            JOIN pg_class child ON i.inhrelid = child.oid
                            WHERE i.inhparent = %s::regclass;
                        """),
                            [full_name],
                        )
                        for part_name, part_bound in cur.fetchall():
                            child_full_name = f"{schema_name}.{part_name}"
                            alter_stmt = (
                                f"ALTER TABLE {full_name} ATTACH PARTITION {child_full_name}"
                            )
                            if part_bound:
                                alter_stmt += f" {part_bound}"
                            alter_stmt += ";"
                            schema_creation_script.append(alter_stmt)

                elif relkind == "v":
                    # Create view.
                    cur.execute(
                        sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"),
                        [full_name],
                    )
                    viewdef = cur.fetchone()[0]
                    schema_creation_script.append(
                        f"CREATE OR REPLACE VIEW {full_name} AS\n{viewdef};"
                    )
                elif relkind == "m":
                    # Create materialized view.
                    cur.execute(
                        sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"),
                        [full_name],
                    )
                    viewdef = cur.fetchone()[0]
                    schema_creation_script.append(
                        f"CREATE MATERIALIZED VIEW {full_name} AS\n{viewdef} WITH DATA;"
                    )

            # -- Now process additional objects in the schema.

            # Sequences (using information_schema so that we get a readable set of attributes)
            cur.execute(
                sql.SQL("""
    SELECT sequence_name, start_value, minimum_value, maximum_value, increment, cycle_option
    FROM information_schema.sequences
    WHERE sequence_schema = %s;
            """),
                [schema_name],
            )
            for (
                seq_name,
                start_value,
                min_value,
                max_value,
                increment,
                cycle_option,
            ) in cur.fetchall():
                seq_stmt = f"CREATE SEQUENCE {schema_name}.{seq_name}\n"
                seq_stmt += f"    START WITH {start_value}\n"
                seq_stmt += f"    INCREMENT BY {increment}\n"
                seq_stmt += f"    MINVALUE {min_value}\n"
                seq_stmt += f"    MAXVALUE {max_value}\n"
                seq_stmt += f"    {'CYCLE' if cycle_option.upper() == 'YES' else 'NO CYCLE'};"
                schema_creation_script.append(seq_stmt)

            # Indexes (query via pg_indexes and join with pg_class 
            # to exclude extension‐owned objects)
            cur.execute(
                sql.SQL("""
                SELECT c.oid, i.indexname, i.indexdef
                FROM pg_indexes i
                JOIN pg_namespace n ON i.schemaname = n.nspname
                JOIN pg_class c ON c.relname = i.indexname AND c.relnamespace = n.oid
                WHERE i.schemaname = %s
                  AND NOT EXISTS (
                      SELECT 1 FROM pg_depend d
                      WHERE d.objid = c.oid AND d.deptype = 'e'
                  );
            """),
                [schema_name],
            )
            for _oid, _indexname, indexdef in cur.fetchall():
                schema_creation_script.append(indexdef + ";")

            # Functions (exclude functions that are part of an extension)
            try:
                cur.execute(
                    sql.SQL("""
                   SELECT p.oid, p.proname,
                        CASE
                            WHEN p.prokind = 'f' THEN pg_get_functiondef(p.oid)
                            WHEN p.prokind = 'a' THEN
                                'Aggregate function using ' || (SELECT pp.proname
                                                                FROM pg_proc pp
                                                                WHERE pp.oid = a.aggtransfn)
                            ELSE ''
                        END AS function_def
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    LEFT JOIN pg_aggregate a ON a.aggfnoid = p.oid  -- Get aggregate details
                    WHERE n.nspname = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM pg_depend d
                        WHERE d.objid = p.oid AND d.deptype = 'e'
                    );
                   """),
                    [schema_name],
                )
                for _oid, _proname, funcdef in cur.fetchall():
                    schema_creation_script.append(funcdef)
            except Exception:
                pass

        return "\n\n".join(schema_creation_script)
