# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Dict, List, Optional, Tuple

import psycopg
from psycopg import (Column, connection, cursor)
from psycopg.pq import TransactionStatus
from ossdbtoolsservice.driver.types import ServerConnection
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace.contracts import Configuration

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


class PostgreSQLConnection(ServerConnection):
    """Wrapper for a psycopg connection that makes various properties easier to access"""

    def __init__(self, conn_params: Dict[str, str], config: Optional[Configuration] = None):
        """
        Creates a new connection wrapper. Parses version string
        :param conn_params: connection parameters dict
        :param config: optional Configuration object with pgsql connection config
        """
        # If options contains azureSecurityToken, then just copy it over to password, which is how it is
        # passed to PostgreSQL.
        if 'azureAccountToken' in conn_params:
            conn_params['password'] = conn_params['azureAccountToken']

        # Map the connection options to their psycopg-specific options
        self._connection_options = connection_options = {PG_CONNECTION_OPTION_KEY_MAP.get(option, option): value for option, value in conn_params.items()
                                                         if option in PG_CONNECTION_PARAM_KEYWORDS}

        # Use the default database if one was not provided
        if 'dbname' not in connection_options or not connection_options['dbname']:
            if config:
                connection_options['dbname'] = config.pgsql.default_database
            else:
                connection_options['dbname'] = constants.DEFAULT_DB[constants.PG_PROVIDER_NAME]

        # Use the default port number if one was not provided
        if 'port' not in connection_options or not connection_options['port']:
            connection_options['port'] = constants.DEFAULT_PORT[constants.PG_PROVIDER_NAME]

        # Pass connection parameters as keyword arguments to the connection by unpacking the connection_options dict
        self._conn = psycopg.connect(**connection_options)

        # Set autocommit mode so that users have control over transactions
        self._conn.autocommit = True

        # Get the DSN parameters for the connection as a dict
        if self._conn.info.dsn is not None:
            # split by spaces unless in quotes or double quotes
            parts = re.split(r'\s(?=(?:(?:[^"\'\\]*(?:\\.|"(?:[^"\\]*\\.)*[^"\\]*"|\'(?:[^\'\\]*\\.)*[^\'\\]*\')*))[^"\'\\]*$)', self._conn.info.dsn)
            
            self._dsn_parameters = {}
            for part in parts:
                if '=' not in part:
                    raise ValueError(f'Malformed DSN string: {self._conn.info.dsn}')
                key, value = part.split('=')

                # Remove quotes or double quotes if they exist
                value = re.sub(r'^[\'"]|[\'"]$', '', value)
                self._dsn_parameters[key] = value
        else:
            self._dsn_parameters = {}

        # Find the class of the database error this driver throws
        self._database_error = psycopg.DatabaseError

        # Calculate the server version
        version_string = str(self._conn.info.server_version)
        self._version: Tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:])
        )

        # Setting the provider for this connection
        self._provider_name = constants.PG_PROVIDER_NAME
        self._server_type = "PostgreSQL"

    # METHODS ##############################################################
    @property
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""
        return self._conn.autocommit

    @property
    def host_name(self) -> str:
        """Returns the hostname for the current connection"""
        return self._dsn_parameters['host']

    @property
    def port(self) -> int:
        """Returns the port number used for the current connection"""
        return self._connection_options["port"]

    @property
    def database_name(self) -> str:
        """Return the name of the current connection's database"""
        return self._dsn_parameters['dbname']

    @property
    def user_name(self) -> str:
        """Returns the user name number used for the current connection"""
        return self._dsn_parameters["user"]

    @property
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        return self._version

    @property
    def server_type(self) -> str:
        """Server type for distinguishing between standard PG and PG supersets"""
        return self._server_type

    @property
    def connection_options(self):
        """ Returns the options used to create the current connection to the server """
        return self._connection_options

    @property
    def default_database(self):
        """Returns the default database for PostgreSQL if no other database is specified"""
        return constants.DEFAULT_DB[self._provider_name]

    @property
    def database_error(self):
        """Returns the type of database error this connection throws"""
        return self._database_error

    @property
    def transaction_in_error(self) -> bool:
        """Returns bool indicating if transaction is in error"""
        return self._conn.TransactionStatus is TransactionStatus.INERROR

    @property
    def query_canceled_error(self) -> Exception:
        """Returns driver query canceled error"""
        return psycopg.errors.QueryCanceled

    @property
    def cancellation_query(self) -> str:
        """Returns a SQL command to end the current query execution process"""
        backend_pid = self._conn.info.backend_pid
        return PG_CANCELLATION_QUERY.format(backend_pid)

    @property
    def connection(self) -> connection:
        """Returns the underlying connection"""
        return self._conn

    @property
    def open(self) -> bool:
        """Returns bool indicating if connection is open"""
        # 0 if the connection is open, nonzero if it is closed or broken.
        return self._conn.closed == 0

    # METHODS ##############################################################
    @autocommit.setter
    def autocommit(self, mode: bool):
        """
        Sets the current autocommit status for this connection
        :param mode: True or False
        """
        self._conn.autocommit = mode

    def commit(self):
        """
        Commits the current transaction
        """
        self._conn.commit()

    def cursor(self, **kwargs):
        """
        Returns a client cursor for the current connection.
        Client cursor is a new cursor introduced in psycopg3 with better performance.
        :param kwargs (optional) to create a named cursor
        """
        return psycopg.ClientCursor(self._conn)

    def execute_query(self, query, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises psycopg.ProgrammingError: if there was no result set when executing the query
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

    def execute_2darray(self, query: str, params=None):
        cur: cursor = self._conn.cursor()

        try:
            cur.execute(query, params)

            # Get Resultset Column Name, Type and size
            columns = cur.description

            rows = []
            self.row_count = cur.rowcount
            if cur.rowcount > 0:
                for row in cur:
                    rows.append(row)
        finally:
            cur.close()

        return {'columns': columns, 'rows': rows}

    def list_databases(self):
        """
        List the databases accessible by the current PostgreSQL connection.
        """
        return self.execute_query('SELECT datname FROM pg_database WHERE datistemplate = false;')

    def get_database_owner(self):
        """
        List the owner(s) of the current database
        """
        database_name = self.database_name
        owner_query = "SELECT pg_catalog.pg_get_userbyid(db.datdba) FROM pg_catalog.pg_database db WHERE db.datname = '{}'".format(database_name)
        return self.execute_query(owner_query, all=True)[0][0]

    def get_database_size(self, dbname: str):
        """
        Gets the size of a particular database in MB
        """

    def get_error_message(self, error) -> str:
        """
        Get the message from DatabaseError instance
        """
        return error.diag.message_primary

    def close(self):
        """
        Closes this current connection.
        """
        self._conn.close()
