# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from pgsqltoolsservice.driver.types import ServerConnection
import pymysql


# Recognized parameter keywords for MySQL connections
# Source: https://dev.mysql.com/doc/refman/8.0/en/connection-options.html
# Source:https://pymysql.readthedocs.io/en/latest/modules/connections.html?highlight=mode
MYSQL_CONNECTION_PARAM_KEYWORDS = [
    'host', 'database', 'user', 'password', 'bind_address', 'port', 'connect_timeout', 
    'read_timeout', 'write_timeout', 'client_flag', 'sql_mode', 'sslmode', 'ssl'
]


class PyMySQLConnection(ServerConnection):
    """Wrapper for a pymysql connection that makes various properties easier to access"""

    def __init__(self, conn_params):
        """
        Creates a new connection wrapper. Parses version string
        :param conn_params: connection parameters dict
        """
        # Map the connection options to their pymysql-specific options
        self._connection_options = {param: conn_params[param] for param in MYSQL_CONNECTION_PARAM_KEYWORDS 
        if param in conn_params.keys()}

        # If SSL is enabled or allowed
        if "ssl" in conn_params.keys() and self._connection_options["ssl"] != "disable":
            # Find all the ssl options (key, ca, cipher)
            ssl_params = {param for param in conn_params if param.startswith("ssl.")}
            
            # Map the ssl option names to their values
            ssl_dict = {param.strip("ssl."):conn_params[param] for param in ssl_params}
            
            # Assign the ssl options to the dict
            self._connection_options["ssl"] = ssl_dict

        # Setting autocommit to True initally
        self._connection_options["autocommit"] = True
        self._autocommit_status = True

        # Pass connection parameters as keyword arguments to the connection by unpacking the connection_options dict
        self._conn = pymysql.connect(**self._connection_options)

        # Check that we connected successfully
        assert type(self._conn) is pymysql.connections.Connection

        # Find the class of the database error this driver throws
        self._database_error = pymysql.err.DatabaseError

        # Calculate the server version
        version_string = self.execute_query("SHOW VARIABLES LIKE 'version';")[0][1]

        # Split the different components of the version string
        import re
        version_components: List = re.split(r"[.-]", version_string)
        self._version: Tuple[int, int, int] = (
            int(version_components[0]),
            int(version_components[1]),
            int(version_components[2])
        )

    ###################### PROPERTIES ##################################
    @property
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""
        return self._autocommit_status

    @property
    def host_name(self) -> str:
        """Returns the hostname for the current connection"""
        return self._connection_options["host"]

    @property
    def port_num(self) -> int:
        """Returns the port number used for the current connection"""
        if "port" in self._connection_options.keys():
            return self._connection_options["port"]
        else:
            return None

    @property
    def user_name(self) -> str:
        """Returns the port number used for the current connection"""
        return self._connection_options["user"]

    @property
    def database_name(self) -> str:
        """Return the name of the current connection's database"""
        return self._connection_options["database"]

    @property
    def server_version(self) -> Tuple[int, int, int]:
        """Returns the server version as a Tuple"""
        return self._version

    @classmethod
    def default_database(cls):
        """Returns the default database for MySQL if no other database is specified"""
        return None

    @property
    def database_error(self):
        """ Returns the type of database error this connection throws"""
        return self._database_error

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
    @autocommit.setter
    def autocommit(self, mode: bool):
        """
        Sets the given autocommit status for this connection
        :param mode: True or False
        """

        # Close our current connection
        self._conn.close()

        # Open a new connection with the given autocommit status
        self._connection_options["autocommit"] = mode
        self._autocommit_status = mode

        # Pass connection parameters as keyword arguments to the connection by unpacking the connection_options dict
        self._conn = pymysql.connect(**self._connection_options)

        # Check that we connected successfully
        assert type(self._conn) is pymysql.connections.Connection
    
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """
        cursor = self._conn.cursor()
        cursor.execute(query)
        if all:
            query_results = cursor.fetchall()
        else:
            query_results = cursor.fetchone()

        cursor.close()
        return query_results
    
    def execute_dict(self, query: str, params=None):
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        raise NotImplementedError("execute_dict has not been implemented.")

    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """
        return self.execute_query('SHOW DATABASES')
    
    def close(self):
        """
        Closes this current connection.
        """
        self._conn.close()