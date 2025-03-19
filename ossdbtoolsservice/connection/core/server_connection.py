# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections.abc import Mapping, Sequence
from typing import Any

import psycopg
from psycopg import Column
from psycopg.pq import TransactionStatus
from psycopg_pool import ConnectionPool

from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.sql import as_sql

PG_CANCELLATION_QUERY = "SELECT pg_cancel_backend ({})"

Params = Sequence[Any] | Mapping[str, Any]


class ServerConnection:
    """Wrapper for a psycopg connection that makes various properties easier to access"""

    def __init__(
        self, connection: psycopg.Connection, pool: ConnectionPool | None = None
    ) -> None:
        """
        Creates a new connection wrapper. Parses version string
        :param conn_params: connection parameters dict
        :param pool: Optional connection pool for this connection.
            This supports cases where the connection is not associated with
            a pooled connection context manager, but the connection needs to be
            returned to a pool. E.g. if the connection is broken, call return_to_pool
            and request a new one.
        """

        # Pass connection parameters as keyword arguments to the
        # connection by unpacking the connection_options dict
        self._conn = connection
        self._pool = pool

        # Set autocommit mode so that users have control over transactions
        self._conn.autocommit = True

        # Set initial transaction is not from user
        self._user_transaction = False

        # Set initial connection has error
        self._transaction_in_error = (
            self._conn.info.transaction_status is TransactionStatus.INERROR
        )

        # Get the DSN parameters for the connection as a dict
        self._dsn_parameters = self._conn.info.get_parameters()

        # Calculate the server version
        version_string = str(self._conn.info.server_version)
        self._version: tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:]),
        )

    # METHODS ##############################################################
    @property
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""
        return self._conn.autocommit

    @autocommit.setter
    def autocommit(self, mode: bool) -> None:
        """
        Sets the current autocommit status for this connection
        :param mode: True or False
        """
        self._conn.autocommit = mode

    @property
    def host_name(self) -> str:
        """Returns the hostname for the current connection"""
        return self._dsn_parameters["host"]

    @property
    def port(self) -> int:
        """Returns the port number used for the current connection"""
        return int(
            self._dsn_parameters.get("port")
            or constants.DEFAULT_PORT[constants.PG_PROVIDER_NAME]
        )

    @property
    def database_name(self) -> str:
        """Return the name of the current connection's database"""
        return self._dsn_parameters["dbname"]

    @property
    def user_name(self) -> str:
        """Returns the user name number used for the current connection"""
        return self._dsn_parameters["user"]

    @property
    def application_name(self) -> str | None:
        """Returns the application name used for the current connection"""
        return self._dsn_parameters.get("application_name")

    @property
    def server_version(self) -> tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        return self._version

    @property
    def transaction_in_error(self) -> bool:
        """Returns bool indicating if transaction is in error"""
        return (
            self._conn.info.transaction_status is TransactionStatus.INERROR
            or self._transaction_in_error
        )

    @property
    def transaction_is_idle(self) -> bool:
        """Returns bool indicating if transaction is currently idle.

        The value TransactionStatus.IDLE indicates that the
        connection is NOT currently in a transaction.
        """
        return self._conn.info.transaction_status is TransactionStatus.IDLE

    @property
    def transaction_in_trans(self) -> bool:
        """Returns bool indicating if transaction is currently in transaction block"""
        return self._conn.info.transaction_status is TransactionStatus.INTRANS

    @property
    def user_transaction(self) -> bool:
        """Returns bool indicating if transaction is in error"""
        return self._user_transaction

    @property
    def cancellation_query(self) -> str:
        """Returns a SQL command to end the current query execution process"""
        backend_pid = self.backend_pid
        return PG_CANCELLATION_QUERY.format(backend_pid)

    @property
    def backend_pid(self) -> int:
        """Returns the backend process id for this connection"""
        return self._conn.info.backend_pid

    @property
    def connection(self) -> psycopg.Connection:
        """Returns the underlying connection"""
        return self._conn

    @property
    def open(self) -> bool:
        """Returns bool indicating if connection is open"""
        # 0 if the connection is open, nonzero if it is closed or broken.
        return self._conn.closed == 0

    # METHODS ##############################################################

    def commit(self) -> None:
        """
        Commits the current transaction
        """
        self._conn.commit()

    def rollback(self) -> None:
        """
        Rollbacks the current transaction
        """
        self._conn.rollback()

    def cursor(self, **kwargs: Any) -> psycopg.ClientCursor[tuple[Any, ...]]:
        """
        Returns a client cursor for the current connection.
        Client cursor is a new cursor introduced in psycopg3 with better performance.
        :param kwargs (optional) to create a named cursor
        """
        # TODO: kwargs are ignored. Do we need named cursors? They were not implemented here.
        # SelectBatch.get_cursor asks for a named cursor.
        if isinstance(self._conn, psycopg.Connection):
            return psycopg.ClientCursor(self._conn)
        else:
            # Handle Mocks for testing. TODO
            return self._conn.cursor()

    def execute_query(
        self, query: str, all: bool = True
    ) -> list[tuple[Any, ...]] | tuple[Any, ...] | None:
        """
        Execute a simple query without arguments for the given connection
        :raises psycopg.ProgrammingError: if there was no result set when executing the query
        """
        if all:
            return self.fetch_all(query)
        else:
            return self.fetch_one(query)

    def execute_statement(self, query: str, params: Params | None = None) -> None:
        """
        Execute a statement that returns no results.
        :raises psycopg.ProgrammingError: if there was no result set when executing the query
        """
        with self.cursor() as cur:
            query_sql = as_sql(query)
            cur.execute(query_sql, params=params)

    def fetch_all(self, query: str, params: Params | None = None) -> list[tuple[Any, ...]]:
        """
        Execute a query for the given connection. Fetch all results.
        :raises psycopg.ProgrammingError: if there was no result set when executing the query
        """
        with self.cursor() as cur:
            query_sql = as_sql(query)
            cur.execute(query_sql, params=params)
            query_results = cur.fetchall()
            return query_results

    def fetch_one(self, query: str, params: Params | None = None) -> tuple[Any, ...] | None:
        """
        Execute a query for the given connection. Fetch a single result.
        :raises psycopg.ProgrammingError: if there was no result set when executing the query
        """
        with self.cursor() as cur:
            query_sql = as_sql(query)
            cur.execute(query_sql, params=params)
            query_results = cur.fetchone()
            return query_results

    def execute_dict(
        self, query: str, params: Params | None = None
    ) -> tuple[list[Column], list[dict[str, Any]]]:
        """
        Executes a query and returns the results as an ordered
        list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        with self.cursor() as cur:
            query_sql = as_sql(query)
            cur.execute(query_sql, params)

            cols: list[Column] | None = cur.description

            rows: list[dict] = []
            if cur.rowcount > 0 and cols is not None:
                for row in cur:
                    row_dict = {cols[ind].name: x for ind, x in enumerate(row)}
                    rows.append(row_dict)

                return cols, rows
            else:
                return cols or [], rows

    def execute_2darray(self, query: str, params: Params | None = None) -> dict[str, Any]:
        with self.cursor() as cur:
            query_sql = as_sql(query)
            cur.execute(query_sql, params)

            # Get Resultset Column Name, Type and size
            columns = cur.description

            rows = []
            self.row_count = cur.rowcount
            if cur.rowcount > 0:
                for row in cur:
                    rows.append(row)

            return {"columns": columns, "rows": rows}

    def list_databases(self) -> list[tuple[Any, ...]]:
        """
        List the databases accessible by the current PostgreSQL connection.
        """
        return self.fetch_all("SELECT datname FROM pg_database WHERE datistemplate = false;")

    def get_database_owner(self) -> Any | Any:
        """
        List the owner(s) of the current database
        """
        database_name = self.database_name
        owner_query = (
            f"SELECT pg_catalog.pg_get_userbyid(db.datdba) "
            "FROM pg_catalog.pg_database db "
            f"WHERE db.datname = '{database_name}'"
        )
        query_result = self.execute_query(owner_query, all=True)
        return query_result[0][0] if query_result else None

    def get_database_size(self, dbname: str) -> Any | None:
        """
        Gets the size of a particular database in MB
        """
        # TODO: Implement or remove.
        return None

    def get_error_message(self, error: Exception) -> str:
        """
        Get the message from DatabaseError instance
        """
        # If error.args exists and has at least one element,
        # return the first element as the error message.
        if hasattr(error, "args") and error.args and len(error.args) > 0:
            return error.args[0]

        # If error.diag.message_primary is not None, return it.
        elif (
            isinstance(error, psycopg.DatabaseError)
            and error.diag
            and error.diag.message_primary
        ):
            return error.diag.message_primary

        # If neither is available, return a generic error message.
        else:
            return "An unspecified database error occurred."

    def close(self) -> None:
        """
        Closes this current connection.
        """
        if not self._conn.closed:
            self._conn.close()
        # If the connection is part of a pool, return it to the pool.
        if self._pool is not None:
            self._pool.putconn(self._conn)

    def return_to_pool(self) -> None:
        """
        Returns this connection to the pool, if it is part of a pool.
        """
        if self._pool is not None:
            self._pool.putconn(self._conn)

    def check(self) -> None:
        """
        Checks the connection. Raises an error if the connection is broken.
        """
        ConnectionPool.check_connection(self._conn)

    def set_transaction_in_error(self) -> None:
        """
        Sets if current connection is in error
        """
        self._transaction_in_error = True

    def set_user_transaction(self, mode: bool) -> None:
        """
        Sets if current connection is user started
        """
        self._user_transaction = mode
