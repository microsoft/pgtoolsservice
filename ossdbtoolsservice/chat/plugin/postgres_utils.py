from typing import Callable

from psycopg import Connection, sql

from ossdbtoolsservice.utils.sql import as_sql


def execute_readonly_query(
    connection: Connection, query: str, max_result_chars: int = 7000
) -> str:
    """Execute a read-only query against the database."""
    with connection.cursor() as cur:
        cur.execute("BEGIN TRANSACTION READ ONLY;")
        try:
            cur.execute(as_sql(query))
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
        cur.execute(as_sql(statement))
        return "Statement executed successfully."


def get_schema_names(connection: Connection) -> list[str]:
    """Return schema names for all schemas."""
    schema_names = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT nspname
                FROM pg_catalog.pg_namespace
                WHERE nspname NOT IN ('pg_catalog', 'information_schema')
                  AND nspname NOT LIKE 'pg_%';
            """)
        )
        schema_names = [row[0] for row in cur.fetchall()]
    return schema_names


def get_table_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return table, view, and materialized view creation scripts for a schema."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
            SELECT c.relname, c.relkind, c.oid
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s
                AND c.relkind IN ('r', 'p', 'f', 'v', 'm')
                AND (c.relkind NOT IN ('r', 'f') 
                    OR c.oid NOT IN (SELECT inhrelid FROM pg_inherits))
            ORDER BY c.relname;
        """),
            [schema_name],
        )
        objects = cur.fetchall()
        for obj_name, relkind, _oid in objects:
            full_name = f"{schema_name}.{obj_name}"
            if relkind in ("r", "p", "f"):
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
                stmt = f"CREATE TABLE {full_name} (\n    " + ",\n    ".join(col_defs) + "\n)"
                if relkind == "p":
                    cur.execute(
                        sql.SQL("SELECT pg_get_partkeydef(%s::regclass);"), [full_name]
                    )
                    partdef_fetch = cur.fetchone()
                    partdef = partdef_fetch[0] if partdef_fetch else None
                    if partdef:
                        stmt += f" PARTITION BY {partdef}"
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
                scripts.append(stmt)
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
                    scripts.append(tgdef + ";")
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
                        scripts.append(alter_stmt)
            elif relkind == "v":
                cur.execute(
                    sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"), [full_name]
                )
                viewdef_fetch = cur.fetchone()
                viewdef = viewdef_fetch[0] if viewdef_fetch else ""
                scripts.append(f"CREATE OR REPLACE VIEW {full_name} AS\n{viewdef};")
            elif relkind == "m":
                cur.execute(
                    sql.SQL("SELECT pg_get_viewdef(%s::regclass, true);"), [full_name]
                )
                viewdef_fetch = cur.fetchone()
                viewdef = viewdef_fetch[0] if viewdef_fetch else ""
                scripts.append(
                    f"CREATE MATERIALIZED VIEW {full_name} AS\n{viewdef} WITH DATA;"
                )
    return scripts


def get_sequence_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return sequence creation scripts for a schema."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
            SELECT sequence_name, start_value, minimum_value, maximum_value, 
                   increment, cycle_option
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
            scripts.append(seq_stmt)
    return scripts


def get_index_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return index creation scripts for a schema."""
    scripts = []
    with connection.cursor() as cur:
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
            scripts.append(indexdef + ";")
    return scripts


def get_function_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return function creation scripts for a schema."""
    scripts = []
    with connection.cursor() as cur:
        try:
            cur.execute(
                sql.SQL("""
                SELECT p.oid, p.proname,
                    CASE
                        WHEN p.prokind = 'f' THEN pg_get_functiondef(p.oid)
                        WHEN p.prokind = 'a' THEN
                            'Aggregate function using ' || 
                            (SELECT pp.proname FROM pg_proc pp WHERE pp.oid = a.aggtransfn)
                        ELSE ''
                    END AS function_def
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                LEFT JOIN pg_aggregate a ON a.aggfnoid = p.oid  
                WHERE n.nspname = %s
                AND NOT EXISTS (
                    SELECT 1 FROM pg_depend d
                    WHERE d.objid = p.oid AND d.deptype = 'e'
                );
            """),
                [schema_name],
            )
            for _oid, _proname, funcdef in cur.fetchall():
                scripts.append(funcdef)
        except Exception:
            pass
    return scripts


def get_table_grant_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return GRANT statements for tables, views, materialized views,
    and partitions in a schema."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT c.relname, a.grantee, string_agg(a.privilege_type, ', ') AS privileges
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                CROSS JOIN LATERAL aclexplode(c.relacl) a
                WHERE n.nspname = %s
                  AND c.relkind IN ('r', 'p', 'f', 'v', 'm')
                GROUP BY c.relname, a.grantee;
            """),
            [schema_name],
        )
        for relname, grantee, privileges in cur.fetchall():
            full_name = f"{schema_name}.{relname}"
            # An empty grantee means PUBLIC
            if grantee == "":
                grantee = "PUBLIC"
            scripts.append(f"GRANT {privileges} ON TABLE {full_name} TO {grantee};")
    return scripts


def get_sequence_grant_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return GRANT statements for sequences in a schema."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT c.relname, a.grantee, string_agg(a.privilege_type, ', ') AS privileges
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                CROSS JOIN LATERAL aclexplode(c.relacl) a
                WHERE n.nspname = %s
                  AND c.relkind = 'S'
                GROUP BY c.relname, a.grantee;
            """),
            [schema_name],
        )
        for relname, grantee, privileges in cur.fetchall():
            full_name = f"{schema_name}.{relname}"
            if grantee == "":
                grantee = "PUBLIC"
            scripts.append(f"GRANT {privileges} ON SEQUENCE {full_name} TO {grantee};")
    return scripts


def get_function_grant_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return GRANT statements for functions in a schema."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT p.proname,
                       pg_get_function_identity_arguments(p.oid) AS args,
                       a.grantee,
                       string_agg(a.privilege_type, ', ') AS privileges
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                CROSS JOIN LATERAL aclexplode(p.proacl) a
                WHERE n.nspname = %s
                GROUP BY p.proname, p.oid, a.grantee;
            """),
            [schema_name],
        )
        for proname, args, grantee, privileges in cur.fetchall():
            full_name = f"{schema_name}.{proname}({args})"
            if grantee == "":
                grantee = "PUBLIC"
            scripts.append(f"GRANT {privileges} ON FUNCTION {full_name} TO {grantee};")
    return scripts


def get_schema_grant_scripts(connection: Connection, schema_name: str) -> list[str]:
    """Return GRANT statements for the schema itself."""
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT nspacl
                FROM pg_namespace
                WHERE nspname = %s;
            """),
            [schema_name],
        )
        row = cur.fetchone()
        if row and row[0]:
            # If nspacl is returned as a string, e.g., "{alice=UC/bob, bob=CU}",
            # strip the curly braces and split on commas to get the ACL items.
            acl_string = row[0].strip("{}")
            acl_items = [item.strip() for item in acl_string.split(",")] if acl_string else []
            for acl in acl_items:
                # Split into grantee and the rights portion
                parts = acl.split("=")
                grantee = parts[0] if parts[0] else "PUBLIC"
                rights_part = parts[1]
                # The privileges are before the slash
                privileges_str = rights_part.split("/")[0]
                # For schemas, privileges are usually 'C' (CREATE) and 'U' (USAGE)
                mapping = {"C": "CREATE", "U": "USAGE"}
                privs = []
                for char in privileges_str:
                    if char in mapping:
                        privs.append(mapping[char])
                if privs:
                    priv_list = ", ".join(privs)
                    scripts.append(f"GRANT {priv_list} ON SCHEMA {schema_name} TO {grantee};")
    return scripts


def get_comment_scripts(connection: Connection, schema_name: str) -> list[str]:
    """
    Generate COMMENT statements for tables, columns, functions, indexes, and the schema.
    """
    scripts = []
    with connection.cursor() as cur:
        # Table comments.
        cur.execute(
            sql.SQL("""
                SELECT c.relname, obj_description(c.oid, 'pg_class') AS comment
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND obj_description(c.oid, 'pg_class') IS NOT NULL;
            """),
            [schema_name],
        )
        for relname, comment in cur.fetchall():
            full_table = f"{schema_name}.{relname}"
            scripts.append(f"COMMENT ON TABLE {full_table} IS '{comment}';")

        # Column comments.
        cur.execute(
            sql.SQL("""
                SELECT c.relname, a.attname, col_description(a.attrelid, a.attnum) AS comment
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND col_description(a.attrelid, a.attnum) IS NOT NULL;
            """),
            [schema_name],
        )
        for relname, attname, comment in cur.fetchall():
            full_name = f"{schema_name}.{relname}"
            scripts.append(f"COMMENT ON COLUMN {full_name}.{attname} IS '{comment}';")

        # Function comments.
        cur.execute(
            sql.SQL("""
                SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args,
                       obj_description(p.oid, 'pg_proc') AS comment
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = %s
                  AND obj_description(p.oid, 'pg_proc') IS NOT NULL;
            """),
            [schema_name],
        )
        for proname, args, comment in cur.fetchall():
            full_func = f"{schema_name}.{proname}({args})"
            scripts.append(f"COMMENT ON FUNCTION {full_func} IS '{comment}';")

        # Index comments.
        cur.execute(
            sql.SQL("""
                SELECT c.relname, obj_description(c.oid, 'pg_class') AS comment
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND c.relkind = 'i'
                  AND obj_description(c.oid, 'pg_class') IS NOT NULL;
            """),
            [schema_name],
        )
        for relname, comment in cur.fetchall():
            full_index = f"{schema_name}.{relname}"
            scripts.append(f"COMMENT ON INDEX {full_index} IS '{comment}';")

        # Schema comment.
        cur.execute(
            sql.SQL("""
                SELECT n.nspname, obj_description(n.oid, 'pg_namespace') AS comment
                FROM pg_namespace n
                WHERE n.nspname = %s
                  AND obj_description(n.oid, 'pg_namespace') IS NOT NULL;
            """),
            [schema_name],
        )
        for nspname, comment in cur.fetchall():
            scripts.append(f"COMMENT ON SCHEMA {nspname} IS '{comment}';")
    return scripts


def get_ownership_scripts(connection: Connection, schema_name: str) -> list[str]:
    """
    Generate ALTER ... OWNER TO statements for tables, views, materialized views,
    sequences, functions, and the schema.
    """
    scripts = []
    with connection.cursor() as cur:
        # Ownership for tables, views, materialized views, and foreign tables.
        cur.execute(
            sql.SQL("""
                SELECT c.relname, pg_get_userbyid(c.relowner) AS owner, c.relkind
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND c.relkind IN ('r', 'p', 'f', 'v', 'm');
            """),
            [schema_name],
        )
        for relname, owner, relkind in cur.fetchall():
            full_name = f"{schema_name}.{relname}"
            if relkind in ("r", "p", "f"):
                scripts.append(f"ALTER TABLE {full_name} OWNER TO {owner};")
            elif relkind == "v":
                scripts.append(f"ALTER VIEW {full_name} OWNER TO {owner};")
            elif relkind == "m":
                scripts.append(f"ALTER MATERIALIZED VIEW {full_name} OWNER TO {owner};")

        # Ownership for sequences.
        cur.execute(
            sql.SQL("""
                SELECT c.relname, pg_get_userbyid(c.relowner) AS owner
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s
                  AND c.relkind = 'S';
            """),
            [schema_name],
        )
        for relname, owner in cur.fetchall():
            full_name = f"{schema_name}.{relname}"
            scripts.append(f"ALTER SEQUENCE {full_name} OWNER TO {owner};")

        # Ownership for functions.
        cur.execute(
            sql.SQL("""
                SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args,
                       pg_get_userbyid(p.proowner) AS owner
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = %s;
            """),
            [schema_name],
        )
        for proname, args, owner in cur.fetchall():
            full_func = f"{schema_name}.{proname}({args})"
            scripts.append(f"ALTER FUNCTION {full_func} OWNER TO {owner};")

        # Ownership for the schema itself.
        cur.execute(
            sql.SQL("""
                SELECT nspname, pg_get_userbyid(nspowner) AS owner
                FROM pg_namespace
                WHERE nspname = %s;
            """),
            [schema_name],
        )
        for nspname, owner in cur.fetchall():
            scripts.append(f"ALTER SCHEMA {nspname} OWNER TO {owner};")
    return scripts


def get_default_privileges_scripts(connection: Connection, schema_name: str) -> list[str]:
    """
    Generate ALTER DEFAULT PRIVILEGES statements.

    This function queries pg_default_acl to obtain default ACL settings in the given schema.
    It groups ACL entries by the role that set them (defaclrole), the grantee,
    and the object type, then produces a corresponding ALTER DEFAULT PRIVILEGES statement.
    """
    scripts = []
    with connection.cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT defaclobjtype,
                       pg_get_userbyid(defaclrole) AS defaclrole,
                       grantee,
                       privilege_type
                FROM pg_default_acl, LATERAL aclexplode(defaclacl)
                WHERE defaclnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s);
            """),
            [schema_name],
        )
        rows = cur.fetchall()
        privileges: dict = {}
        for objtype, defaclrole, grantee, privilege in rows:
            grantee = grantee if grantee != "" else "PUBLIC"
            key = (defaclrole, grantee, objtype)
            privileges.setdefault(key, set()).add(privilege)
        type_mapping = {"r": "TABLES", "S": "SEQUENCES", "f": "FUNCTIONS"}
        for (defaclrole, grantee, objtype), priv_set in privileges.items():
            obj_word = type_mapping.get(objtype, "TABLES")
            privs = ", ".join(sorted(priv_set))
            stmt = (
                f"ALTER DEFAULT PRIVILEGES FOR ROLE {defaclrole} IN SCHEMA {schema_name} "
                f"GRANT {privs} ON {obj_word} TO {grantee};"
            )
            scripts.append(stmt)
    return scripts


def format_options(options: list[str]) -> str:
    """
    Helper function to format an array of options from PostgreSQL into a string
    suitable for an OPTIONS clause. Assumes each option is in the form key=value.
    """
    formatted = []
    for opt in options:
        if "=" in opt:
            key, value = opt.split("=", 1)
            formatted.append(f"{key} '{value}'")
        else:
            formatted.append(opt)
    return ", ".join(formatted)


def get_fdw_scripts(connection: Connection) -> list[str]:
    """
    Generate scripts for Foreign-Data Wrappers, Foreign Servers, and User Mappings.

    Note: FDW objects are not schema–scoped so they are handled globally.
    """
    scripts = []
    with connection.cursor() as cur:
        # Foreign Data Wrappers.
        cur.execute(
            sql.SQL("""
                SELECT fdwname, 
                       CASE WHEN fdwhandler = 0 THEN NULL 
                        ELSE fdwhandler::regproc END AS fdwhandler,
                       CASE WHEN fdwvalidator = 0 THEN NULL 
                        ELSE fdwvalidator::regproc END AS fdwvalidator,
                       fdwoptions
                FROM pg_foreign_data_wrapper;
            """)
        )
        for fdwname, fdwhandler, fdwvalidator, fdwoptions in cur.fetchall():
            stmt = f"CREATE FOREIGN DATA WRAPPER {fdwname}"
            if fdwhandler:
                stmt += f" HANDLER {fdwhandler}"
            if fdwvalidator:
                stmt += f" VALIDATOR {fdwvalidator}"
            if fdwoptions and len(fdwoptions) > 0:
                opts_str = format_options(fdwoptions)
                stmt += f" OPTIONS ({opts_str})"
            stmt += ";"
            scripts.append(stmt)

        # Foreign Servers.
        cur.execute(
            sql.SQL("""
                SELECT srvname, srvfdw, srvoptions
                FROM pg_foreign_server;
            """)
        )
        for srvname, srvfdw, srvoptions in cur.fetchall():
            stmt = f"CREATE SERVER {srvname} FOREIGN DATA WRAPPER {srvfdw}"
            if srvoptions and len(srvoptions) > 0:
                opts_str = format_options(srvoptions)
                stmt += f" OPTIONS ({opts_str})"
            stmt += ";"
            scripts.append(stmt)

        # User Mappings.
        cur.execute(
            sql.SQL("""
                SELECT um.umuser, um.srvid, um.umoptions, s.srvname
                FROM pg_user_mappings um
                JOIN pg_foreign_server s ON um.srvid = s.oid;
            """)
        )
        for umuser, _srvid, umoptions, srvname in cur.fetchall():
            if umuser == 0:
                user_name: str | None = "PUBLIC"
            else:
                cur.execute("SELECT pg_get_userbyid(%s);", [umuser])
                result = cur.fetchone()
                user_name = str(result[0]) if result else None
            if user_name is not None:
                stmt = f"CREATE USER MAPPING FOR {user_name} SERVER {srvname}"
                if umoptions and len(umoptions) > 0:
                    opts_str = format_options(umoptions)
                    stmt += f" OPTIONS ({opts_str})"
                stmt += ";"
                scripts.append(stmt)
    return scripts


def fetch_full_schema(connection: Connection) -> str:
    """
    Fetch a complete schema creation script by assembling outputs
    from specialized helper functions.
    """
    with connection.cursor() as cur:
        schema_creation_script = []

        def try_extend(name: str, script_part: Callable[[], str]) -> None:
            try:
                script = script_part()
                if script:
                    schema_creation_script.append(script)
            except Exception as e:
                schema_creation_script.append(f"-- Error fetching {name}: {str(e)}")

        # PostgreSQL version.
        cur.execute("SELECT version();")
        version = cur.fetchone()
        if version:
            schema_creation_script.append(f"-- PostgreSQL version: {version[0]}")

        # Extensions.
        cur.execute("SELECT extname FROM pg_extension;")
        for (extname,) in cur.fetchall():
            schema_creation_script.append(f"CREATE EXTENSION IF NOT EXISTS {extname};")

        # Process each non-system schema.
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
              AND schema_name NOT LIKE 'pg_%';
        """)
        schemas = cur.fetchall()
        for (schema_name,) in schemas:
            schema_creation_script.append(f"CREATE SCHEMA {schema_name};")

            # type ignores for "Cannot infer type of lambda  [misc]"

            try_extend(
                "table_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_table_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "sequence_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_sequence_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "index_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_index_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "function_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_function_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "table_grant_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_table_grant_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "sequence_grant_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_sequence_grant_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "function_grant_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_function_grant_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "schema_grant_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_schema_grant_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "comment_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_comment_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "ownership_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_ownership_scripts(connection, schema_name)
                ),
            )
            try_extend(
                "default_privileges_scripts",
                lambda schema_name=schema_name: "\n\n".join(  # type: ignore[misc]
                    get_default_privileges_scripts(connection, schema_name)
                ),
            )

        try_extend("fdw_scripts", lambda: "\n\n".join(get_fdw_scripts(connection)))

    return "\n\n".join(schema_creation_script)
