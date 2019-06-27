# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from pgsqltoolsservice.driver.types import ServerConnection
import pymysql

class PyMySQLConnection(ServerConnection):
    """Wrapper for a pymysql connection that makes various properties easier to access"""
    
    def __init__(self, connection_options):
        """
        Creates a new connection wrapper. Parses version string
        :param connection_options: PsycoPG2 connection options dict
        """
        self._conn = pymysql.connect(**connection_options)
        assert self._conn is type(pymysql.connections.Connection)
        print("Connection to MySQL server established!")

    ###################### PROPERTIES ##################################
    @property
    def connection(self):
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

    @classmethod
    def default_database(cls):
        """Returns the default database for MySQL if no other database is specified"""
        return None

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
    
    def execute_dict(self, query: str, params=None):
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