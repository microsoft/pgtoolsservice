# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from pgsqltoolsservice.driver.types import ServerConnection
import psycopg2
from psycopg2.extensions import Column, connection, cursor, TRANSACTION_STATUS_INERROR

PG_SEARCH_PATH_QUERY = 'SELECT * FROM unnest(current_schemas(true))'
PG_SEARCH_PATH_QUERY_FALLBACK = 'SELECT * FROM current_schemas(true)'
PG_CANCELLATION_QUERY = 'SELECT pg_cancel_backend ({})'

# Dictionary mapping connection option names to their corresponding PostgreSQL connection string keys.
# If a name is not present in this map, the name should be used as the key.
PG_CONNECTION_OPTION_KEY_MAP = {
    'connectTimeout': 'connect_timeout',
    'clientEncoding': 'client_encoding',
    'applicationName': 'application_name'
}

# Recognized parameter keywords for postgres database connection
# Source: https://www.postgresql.org/docs/9.6/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
PG_CONNECTION_PARAM_KEYWORDS = [
    'host', 'hostaddr', 'port', 'dbname', 'user', 'password', 'passfile', 'connect_timeout',
    'client_encoding', 'options', 'application_name', 'fallback_application_name', 'keepalives',
    'keepalives_idle', 'keepalives_interval', 'keepalives_count', 'tty', 'sslmode', 'requiressl',
    'sslcompression', 'sslcert', 'sslkey', 'sslrootcert', 'sslcrl', 'requirepeer', 'krbsrvname',
    'gsslib', 'service', 'target_session_attrs'
]


class PsycopgConnection(ServerConnection):
    """Wrapper for a psycopg2 connection that makes various properties easier to access"""

    def __init__(self, conn_params):
        """
        Creates a new connection wrapper. Parses version string
        :param conn_params: connection parameters
        """
        # Map the connection options to their psycopg2-specific options
        connection_options = {PG_CONNECTION_OPTION_KEY_MAP.get(option, option): value for option, value in conn_params 
        if option in PG_CONNECTION_PARAM_KEYWORDS}

        # Pass connection parameters as keyword arguments to the connection by unpacking the connection_options dict
        self._conn = psycopg2.connect(**connection_options)

        # Check that we connected successfully
        assert self._conn is type(connection)

        # Get the DSN parameters for the connection as a dict
        self._dsn_parameters = self._conn.get_dsn_parameters()

        # Find the class of the database error this driver throws
        self.database_error = psycopg2.DatabaseError

        # Calculate the server version
        version_string = str(self._conn.server_version)
        self._version: Tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:])
        )

    ###################### PROPERTIES ##################################
    @property
    def connection(self):
        """The psycopg2 connection that this object wraps"""
        return self._conn

    @property
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""
        return self._conn.autocommit

    @property
    def dsn_parameters(self) -> Mapping[str, str]:
        """DSN properties of the underlying connection"""
        return self._dsn_parameters

    @property
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        return self._version

    @classmethod
    def default_database(cls):
        """Returns the default database for PostgreSQL if no other database is specified"""
        return "postgres"

    @property
    def search_path_query(self) -> str:
        return PG_SEARCH_PATH_QUERY

    @property
    def search_path_query_fallback(self) -> str:
        return PG_SEARCH_PATH_QUERY_FALLBACK
    
    @property
    def transaction_in_error(self) -> bool:
        return self._conn.get_transaction_status() is psycopg2.extensions.TRANSACTION_STATUS_INERROR
    
    @property
    def cancellation_query(self) -> str:
        backend_pid = self._conn.get_backend_pid()
        return PG_CANCELLATION_QUERY.format(backend_pid)

    ############################# METHODS ##################################
    @autocommit.setter
    def autocommit(self, value: bool):
        """Returns the current autocommit status for this connection"""
        self._conn.autocommit = value
    
    def execute_query(self, query, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises psycopg2.ProgrammingError: if there was no result set when executing the query
        """
        cursor = self._conn.cursor()
        cursor.execute(query)
        if all:
            query_results = cursor.fetchall()
        else:
            query_results = cursor.fetchone()

        cursor.close()
        return query_results

    def execute_dict(self, query: str, params=None) -> Tuple[List[Column], List[dict]]:
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        cur: cursor = self._conn.cursor()

        try:
            cur.execute(query, params)

            cols: List[Column] = cur.description
            rows: List[dict] = []
            if cur.rowcount > 0:
                for row in cur:
                    row_dict = {cols[ind].name: x for ind, x in enumerate(row)}
                    rows.append(row_dict)

            return cols, rows
        finally:
            cur.close()

    def list_databases(self):
        """
        List the databases accessible by the current PostgreSQL connection.
        """
        return self.execute_query('SELECT datname FROM pg_database WHERE datistemplate = false;')

    def close(self):
        """
        Closes this current connection.
        """
        self._conn.close()