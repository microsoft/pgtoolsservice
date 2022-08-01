# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger  # noqa
import pymysql

from ossdbtoolsservice.driver import ServerConnection


class MySQLLightweightMetadata:

    databases_query = '''SHOW DATABASES'''

    tables_query = '''SHOW TABLES'''

    version_query = '''SELECT @@VERSION'''

    version_comment_query = '''SELECT @@VERSION_COMMENT'''
    version_comment_query_mysql4 = '''SHOW VARIABLES LIKE "version_comment"'''

    show_candidates_query = '''SELECT name FROM mysql.help_topic WHERE name LIKE "SHOW %"'''

    users_query = '''SELECT CONCAT("'", user, "'@'",host,"'") FROM mysql.user'''

    functions_query = '''SELECT routine_name FROM information_schema.routines
                            WHERE routine_type="FUNCTION" AND routine_schema = "%s"'''

    table_columns_query = '''SELECT table_name, column_name FROM information_schema.columns
                                WHERE table_schema = '%s'
                                ORDER BY table_name, ordinal_position'''

    def __init__(self, conn: ServerConnection, logger: Logger = None):
        self.conn = conn
        self.logger: Logger = logger
        self.dbname = conn.database_name

    def _log(self, is_error: bool, msg: str, *args) -> None:
        if self.logger is not None:
            if is_error:
                self.logger.error(msg, *args)
            else:
                self.logger.debug(msg, *args)

    """
    Performs lightweight metadata queries to avoid doing full object queries for properties that are
    just needed for intellisense
    """

    def tables(self):
        """Yields table names"""
        with self.conn.cursor() as cur:
            self._log(False, 'Tables Query. sql: %r', self.tables_query)
            cur.execute(self.tables_query)
            for row in cur:
                yield row

    def table_columns(self):
        """Yields (table name, column name) pairs"""
        with self.conn.cursor() as cur:
            self._log(False, 'Columns Query. sql: %r', self.table_columns_query)
            cur.execute(self.table_columns_query % self.dbname)
            for row in cur:
                yield row

    def databases(self):
        with self.conn.cursor() as cur:
            self._log(False, 'Databases Query. sql: %r', self.databases_query)
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]

    def functions(self):
        """Yields tuples of (schema_name, function_name)"""

        with self.conn.cursor() as cur:
            self._log(False, 'Functions Query. sql: %r', self.functions_query)
            cur.execute(self.functions_query % self.dbname)
            for row in cur:
                yield row

    def show_candidates(self):
        with self.conn.cursor() as cur:
            self._log('Show Query. sql: %r', self.show_candidates_query)
            try:
                cur.execute(self.show_candidates_query)
            except pymysql.DatabaseError as e:
                self._log(True, 'No show completions due to %r', e)
                yield ''
            else:
                for row in cur:
                    yield (row[0].split(None, 1)[-1], )

    def users(self):
        with self.conn.cursor() as cur:
            self._log('Users Query. sql: %r', self.users_query)
            try:
                cur.execute(self.users_query)
            except pymysql.DatabaseError as e:
                self._log(True, 'No user completions due to %r', e)
                yield ''
            else:
                for row in cur:
                    yield row
