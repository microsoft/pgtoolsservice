# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from abc import ABC, abstractmethod

import psycopg2
from psycopg2.extensions import Column, connection, cursor, TRANSACTION_STATUS_INERROR      # noqa

PG_SEARCH_PATH_QUERY = 'SELECT * FROM unnest(current_schemas(true))'
PG_SEARCH_PATH_QUERY_FALLBACK = 'SELECT * FROM current_schemas(true)'
PG_CANCELLATION_QUERY = 'SELECT pg_cancel_backend ({})'

class ServerConnection(ABC):
    """Abstract base class that outlines methods and properties that connections must implement"""

    ###################### PROPERTIES ##################################
    @property
    @abstractmethod
    def connection(self) -> connection:
        """The underlying connection object that this object wraps"""
        pass
    
    @property
    @abstractmethod
    def autocommit_status(self) -> bool:
        """Returns the current autocommit status for this connection"""
        pass

    @property
    @abstractmethod
    def dsn_parameters(self) -> Mapping[str, str]:
        """DSN properties of the underlying connection"""
        pass

    @property
    @abstractmethod
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        pass

    @property
    @abstractmethod
    def search_path_query(self) -> str:
        pass

    @property
    @abstractmethod
    def search_path_query_fallback(self) -> str:
        pass

    @property
    @abstractmethod
    def transaction_in_error(self) -> bool:
        pass

    @property
    @abstractmethod
    def cancellation_query(self) -> str:
        pass
    
    ############################# METHODS ##################################
    @abstractmethod
    def set_autocommit(self, mode: bool):
        """
        Sets the connection's autocommit setting to the specified mode
        :param mode: True or False
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """
        pass

    @abstractmethod
    def execute_dict(self, query: str, params=None) -> Tuple[List[Column], List[dict]]:
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        pass
    
    @abstractmethod
    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """
        pass
    
    @abstractmethod
    def close(self):
        """
        Closes this current connection.
        """
        pass
    

class PsycopgConnection(ServerConnection):
    """Wrapper for a psycopg2 connection that makes various properties easier to access"""

    def __init__(self, connection_options):
        """
        Creates a new connection wrapper. Parses version string
        :param connection_options: PsycoPG2 connection options dict
        """
        self._conn = psycopg2.connect(connection_options)
        self._dsn_parameters = self._conn.get_dsn_parameters()
        self.database_error = psycopg2.DatabaseError

        # Calculate the server version
        version_string = str(self._conn.server_version)
        self._version: Tuple[int, int, int] = (
            int(version_string[:-4]),
            int(version_string[-4:-2]),
            int(version_string[-2:])
        )
        return None

    ###################### PROPERTIES ##################################
    @property
    def connection(self) -> connection:
        """The psycopg2 connection that this object wraps"""
        return self._conn

    @property
    def autocommit_status(self) -> bool:
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
    def set_autocommit(self, mode: bool):
        """
        Sets the connection's autocommit setting to the specified mode
        :param mode: True or False
        """
        assert mode in [True, False]
        self._conn.autocommit = mode
    
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


class PyMySQLConnection(ServerConnection):
    """Wrapper for a pymysql connection that makes various properties easier to access"""
    
    def __init__(self, parameter_list):
        pass

    ###################### PROPERTIES ##################################
    @property
    def connection(self) -> connection:
        """The underlying connection object that this object wraps"""
        pass
    
    @property
    def autocommit_status(self) -> bool:
        """Returns the current autocommit status for this connection"""
        pass

    @property
    def dsn_parameters(self) -> Mapping[str, str]:
        """DSN properties of the underlying connection"""
        pass

    @property
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        pass

    @property
    def search_path_query(self) -> str:
        pass

    @property
    def search_path_query_fallback(self) -> str:
        pass
    
    @property
    def transaction_in_error(self) -> int:
        pass

    @property
    def cancellation_query(self) -> str:
        pass

    ############################# METHODS ##################################
    def set_autocommit(self, mode: bool):
        pass
    
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """
        pass
    
    def execute_dict(self, query: str, params=None) -> Tuple[List[Column], List[dict]]:
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        pass

    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """
        pass
    
    def close(self):
        """
        Closes this current connection.
        """
        pass


class DriverManager:
    """Wrapper class that handles different types of drivers and connections """
    
    def __init__(self, provider: str):
        self._provider = provider

    def get_connection(self, **params) -> ServerConnection:
        if self._provider == "PGSQL":
            return PsycopgConnection(params)
        elif self._provider == "MYSQL" or self._provider == "MARIADB":
            return PyMySQLConnection(params)
        else:
            raise AssertionError(self._provider + " is not a supported database engine.")
