# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger  # noqa

from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.language.completion.packages.parseutils.pg_utils.meta import (  # noqa
    ForeignKey, FunctionMetadata)



class PGLightweightMetadata:

    # The boolean argument to the current_schemas function indicates whether
    # implicit schemas, e.g. pg_catalog
    search_path_query = '''
        SELECT * FROM unnest(current_schemas(true))'''

    schemata_query = '''
        SELECT  nspname
        FROM    pg_catalog.pg_namespace
        ORDER BY 1 '''

    tables_query = '''
        SELECT  n.nspname schema_name,
                c.relname table_name
        FROM    pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_namespace n
                    ON n.oid = c.relnamespace
        WHERE   c.relkind = ANY(%s)
        ORDER BY 1,2;'''

    databases_query = '''
        SELECT d.datname
        FROM pg_catalog.pg_database d
        ORDER BY 1'''

    def __init__(self, conn: ServerConnection, logger: Logger = None):
        self.conn = conn
        self._logger: Logger = logger

    def _log(self, message):
        if self._logger:
            self._logger.debug(message)

    """
    Performs lightweight metadata queries to avoid doing full object queries for properties that are
    just needed for intellisense
    """

    def _relations(self, kinds=('r', 'v', 'm')):
        """Get table or view name metadata

        :param kinds: list of postgres relkind filters:
                'r' - table
                'v' - view
                'm' - materialized view
        :return: (schema_name, rel_name) tuples
        """

        with self.conn.cursor() as cur:
            sql = cur.mogrify(self.tables_query, [kinds])
            self._log(f'Tables Query. sql: {sql}')
            cur.execute(sql)
            for row in cur:
                yield row

    def tables(self):
        """Yields (schema_name, table_name) tuples"""
        for row in self._relations(kinds=['r']):
            yield row

    def views(self):
        """Yields (schema_name, view_name) tuples.

            Includes both views and and materialized views
        """
        for row in self._relations(kinds=['v', 'm']):
            yield row

    def _columns(self, kinds=('r', 'v', 'm')):
        """Get column metadata for tables and views

        :param kinds: kinds: list of postgres relkind filters:
                'r' - table
                'v' - view
                'm' - materialized view
        :return: list of (schema_name, relation_name, column_name, column_type) tuples
        """

        if self.conn.connection.server_version >= 80400:
            columns_query = '''
                SELECT  nsp.nspname schema_name,
                        cls.relname table_name,
                        att.attname column_name,
                        att.atttypid::regtype::text type_name,
                        att.atthasdef AS has_default,
                        def.adsrc as default
                FROM    pg_catalog.pg_attribute att
                        INNER JOIN pg_catalog.pg_class cls
                            ON att.attrelid = cls.oid
                        INNER JOIN pg_catalog.pg_namespace nsp
                            ON cls.relnamespace = nsp.oid
                        LEFT OUTER JOIN pg_attrdef def
                            ON def.adrelid = att.attrelid
                            AND def.adnum = att.attnum
                WHERE   cls.relkind = ANY(%s)
                        AND NOT att.attisdropped
                        AND att.attnum  > 0
                ORDER BY 1, 2, att.attnum'''
        else:
            columns_query = '''
                SELECT  nsp.nspname schema_name,
                        cls.relname table_name,
                        att.attname column_name,
                        typ.typname type_name,
                        NULL AS has_default,
                        NULL AS default
                FROM    pg_catalog.pg_attribute att
                        INNER JOIN pg_catalog.pg_class cls
                            ON att.attrelid = cls.oid
                        INNER JOIN pg_catalog.pg_namespace nsp
                            ON cls.relnamespace = nsp.oid
                        INNER JOIN pg_catalog.pg_type typ
                            ON typ.oid = att.atttypid
                WHERE   cls.relkind = ANY(%s)
                        AND NOT att.attisdropped
                        AND att.attnum  > 0
                ORDER BY 1, 2, att.attnum'''

        with self.conn.cursor() as cur:
            sql = cur.mogrify(columns_query, [kinds])
            self._log(f'Columns Query. sql: {sql}')
            cur.execute(sql)
            for row in cur:
                yield row

    def table_columns(self):
        for row in self._columns(kinds=['r']):
            yield row

    def view_columns(self):
        for row in self._columns(kinds=['v', 'm']):
            yield row

    def databases(self):
        with self.conn.cursor() as cur:
            self._log(f'Databases Query. sql: {self.databases_query}')
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]

    def foreignkeys(self):
        """Yields ForeignKey named tuples"""

        if self.conn.connection.server_version < 90000:
            return

        with self.conn.cursor() as cur:
            query = '''
                SELECT s_p.nspname AS parentschema,
                       t_p.relname AS parenttable,
                       unnest((
                        select
                            array_agg(attname ORDER BY i)
                        from
                            (select unnest(confkey) as attnum, generate_subscripts(confkey, 1) as i) x
                            JOIN pg_catalog.pg_attribute c USING(attnum)
                            WHERE c.attrelid = fk.confrelid
                        )) AS parentcolumn,
                       s_c.nspname AS childschema,
                       t_c.relname AS childtable,
                       unnest((
                        select
                            array_agg(attname ORDER BY i)
                        from
                            (select unnest(conkey) as attnum, generate_subscripts(conkey, 1) as i) x
                            JOIN pg_catalog.pg_attribute c USING(attnum)
                            WHERE c.attrelid = fk.conrelid
                        )) AS childcolumn
                FROM pg_catalog.pg_constraint fk
                JOIN pg_catalog.pg_class      t_p ON t_p.oid = fk.confrelid
                JOIN pg_catalog.pg_namespace  s_p ON s_p.oid = t_p.relnamespace
                JOIN pg_catalog.pg_class      t_c ON t_c.oid = fk.conrelid
                JOIN pg_catalog.pg_namespace  s_c ON s_c.oid = t_c.relnamespace
                WHERE fk.contype = 'f';
                '''
            self._log(f'Functions Query. sql: {query}')
            cur.execute(query)
            for row in cur:
                yield ForeignKey(*row)

    def functions(self):
        """Yields FunctionMetadata named tuples"""

        if self.conn.connection.server_version > 90000:
            query = '''
                SELECT n.nspname schema_name,
                        p.proname func_name,
                        p.proargnames,
                        COALESCE(proallargtypes::regtype[], proargtypes::regtype[])::text[],
                        p.proargmodes,
                        prorettype::regtype::text return_type,
                        p.proisagg is_aggregate,
                        p.proiswindow is_window,
                        p.proretset is_set_returning,
                        pg_get_expr(proargdefaults, 0) AS arg_defaults
                FROM pg_catalog.pg_proc p
                        INNER JOIN pg_catalog.pg_namespace n
                            ON n.oid = p.pronamespace
                WHERE p.prorettype::regtype != 'trigger'::regtype
                ORDER BY 1, 2
                '''
        elif self.conn.connection.server_version >= 80400:
            query = '''
                SELECT n.nspname schema_name,
                        p.proname func_name,
                        p.proargnames,
                        COALESCE(proallargtypes::regtype[], proargtypes::regtype[])::text[],
                        p.proargmodes,
                        prorettype::regtype::text,
                        p.proisagg is_aggregate,
                        false is_window,
                        p.proretset is_set_returning,
                        NULL AS arg_defaults
                FROM pg_catalog.pg_proc p
                INNER JOIN pg_catalog.pg_namespace n
                ON n.oid = p.pronamespace
                WHERE p.prorettype::regtype != 'trigger'::regtype
                ORDER BY 1, 2
                '''
        else:
            query = '''
                SELECT n.nspname schema_name,
                        p.proname func_name,
                        p.proargnames,
                        NULL arg_types,
                        NULL arg_modes,
                        '' ret_type,
                        p.proisagg is_aggregate,
                        false is_window,
                        p.proretset is_set_returning,
                        NULL AS arg_defaults
                FROM pg_catalog.pg_proc p
                INNER JOIN pg_catalog.pg_namespace n
                ON n.oid = p.pronamespace
                WHERE p.prorettype::regtype != 'trigger'::regtype
                ORDER BY 1, 2
                '''

        with self.conn.cursor() as cur:
            self._log(f'Functions Query. sql:{query}')
            cur.execute(query)
            for row in cur:
                yield FunctionMetadata(*row)

    def datatypes(self):
        """Yields tuples of (schema_name, type_name)"""

        with self.conn.cursor() as cur:
            if self.conn.connection.server_version > 90000:
                query = '''
                    SELECT n.nspname schema_name,
                           t.typname type_name
                    FROM   pg_catalog.pg_type t
                           INNER JOIN pg_catalog.pg_namespace n
                              ON n.oid = t.typnamespace
                    WHERE ( t.typrelid = 0  -- non-composite types
                            OR (  -- composite type, but not a table
                                  SELECT c.relkind = 'c'
                                  FROM pg_catalog.pg_class c
                                  WHERE c.oid = t.typrelid
                                )
                          )
                          AND NOT EXISTS( -- ignore array types
                                SELECT  1
                                FROM    pg_catalog.pg_type el
                                WHERE   el.oid = t.typelem AND el.typarray = t.oid
                              )
                          AND n.nspname <> 'pg_catalog'
                          AND n.nspname <> 'information_schema'
                    ORDER BY 1, 2;
                    '''
            else:
                query = '''
                    SELECT n.nspname schema_name,
                      pg_catalog.format_type(t.oid, NULL) type_name
                    FROM pg_catalog.pg_type t
                         LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
                    WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
                      AND t.typname !~ '^_'
                          AND n.nspname <> 'pg_catalog'
                          AND n.nspname <> 'information_schema'
                      AND pg_catalog.pg_type_is_visible(t.oid)
                    ORDER BY 1, 2;
                '''
            self._log(f'Datatypes Query. sql: {query}')
            cur.execute(query)
            for row in cur:
                yield row

    def casing(self):
        """Yields the most common casing for names used in db functions"""
        with self.conn.cursor() as cur:
            query = r'''
          WITH Words AS (
                SELECT regexp_split_to_table(prosrc, '\W+') AS Word, COUNT(1)
                FROM pg_catalog.pg_proc P
                JOIN pg_catalog.pg_namespace N ON N.oid = P.pronamespace
                JOIN pg_catalog.pg_language L ON L.oid = P.prolang
                WHERE L.lanname IN ('sql', 'plpgsql')
                AND N.nspname NOT IN ('pg_catalog', 'information_schema')
                GROUP BY Word
            ),
            OrderWords AS (
                SELECT Word,
                    ROW_NUMBER() OVER(PARTITION BY LOWER(Word) ORDER BY Count DESC)
                FROM Words
                WHERE Word ~* '.*[a-z].*'
            ),
            Names AS (
                --Column names
                SELECT attname AS Name
                FROM pg_catalog.pg_attribute
                UNION -- Table/view names
                SELECT relname
                FROM pg_catalog.pg_class
                UNION -- Function names
                SELECT proname
                FROM pg_catalog.pg_proc
                UNION -- Type names
                SELECT typname
                FROM pg_catalog.pg_type
                UNION -- Schema names
                SELECT nspname
                FROM pg_catalog.pg_namespace
                UNION -- Parameter names
                SELECT unnest(proargnames)
                FROM pg_proc
            )
            SELECT Word
            FROM OrderWords
            WHERE LOWER(Word) IN (SELECT Name FROM Names)
            AND Row_Number = 1;
            '''
            self._log(f'Casing Query. sql: {query}')
            cur.execute(query)
            for row in cur:
                yield row[0]
