# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger  # noqa

from ossdbtoolsservice.driver import ServerConnection
from ossdbtoolsservice.language.completion.packages.parseutils.meta import ColumnMetadata, ForeignKey, FunctionMetadata     # noqa

class MySQLLightweightMetadata:

    # The boolean argument to the current_schemas function indicates whether
    # implicit schemas, e.g. pg_catalog
    search_path_query = '''
    '''

    schemata_query = '''
    '''

    tables_query = '''
    '''

    databases_query = '''
    '''

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
        pass

    def tables(self):
        """Yields (schema_name, table_name) tuples"""
        return []


    def views(self):
        """Yields (schema_name, view_name) tuples.

            Includes both views and and materialized views
        """
        return []


    def _columns(self, kinds=('r', 'v', 'm')):
        """Get column metadata for tables and views

        :param kinds: kinds: list of postgres relkind filters:
                'r' - table
                'v' - view
                'm' - materialized view
        :return: list of (schema_name, relation_name, column_name, column_type) tuples
        """
        pass

    def table_columns(self):
        return []

    def view_columns(self):
        return []

    def databases(self):
        return []

    def foreignkeys(self):
        """Yields ForeignKey named tuples"""
        return []

    def functions(self):
        """Yields FunctionMetadata named tuples"""
        return []


    def datatypes(self):
        """Yields tuples of (schema_name, type_name)"""
        return []


    def casing(self):
        """Yields the most common casing for names used in db functions"""
        return []
