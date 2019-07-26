# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from pgsqltoolsservice.driver.types import ServerConnection
import re
import pymysql

# Recognized parameter keywords for MySQL connections
# Source: https://dev.mysql.com/doc/refman/8.0/en/connection-options.html

MYSQL_CONNECTION_OPTION_KEY_MAP = {
    'dbname':'database',
    'connectTimeout': 'connect_timeout',
    'bindAddress': 'bind_address',
    'readTimeout': 'read_timeout',
    'writeTimeout': 'write_timeout',
    'sqlMode': 'sql_mode',
    'clientFlag': 'client_flag'
}

# Source:https://pymysql.readthedocs.io/en/latest/modules/connections.html
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
        # Map the provided connection parameter names to pymysql param names
        _params = {MYSQL_CONNECTION_OPTION_KEY_MAP.get(param, param) : value for param, value in conn_params.items()}

        # Filter the parameters to only those accepted by PyMySQL
        self._connection_options = {param: value for param, value in _params.items() if param in MYSQL_CONNECTION_PARAM_KEYWORDS}

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
        # Source: https://stackoverflow.com/questions/8987679/how-to-retrieve-the-current-version-of-a-mysql-database
        version_string = self.execute_query("SELECT VERSION();")[0][0]

        # Split the different components of the version string
        import re
        version_components: List = re.split(r"[.-]", version_string)
        self._version: Tuple[int, int, int] = (
            int(version_components[0]),
            int(version_components[1]),
            int(version_components[2])
        )
        self._connection_closed = False

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

    @property
    def connection_options(self):
        """ Returns the options used to create the current connection to the server """
        return self._connection_options

    @classmethod
    def default_database(cls):
        """Returns the default database for MySQL if no other database is specified"""
        return "mysql"

    @property
    def database_error(self):
        """ Returns the type of database error this connection throws"""
        return self._database_error

    @property
    def transaction_in_error(self) -> int:
        pass

    @property
    def cancellation_query(self) -> str:
        pass

    def connection_closed(self) -> str:
        return self._connection_closed

    ############################# METHODS ##################################
    @autocommit.setter
    def autocommit(self, mode: bool):
        """
        Sets the given autocommit status for this connection
        :param mode: True or False
        """
        pass
        # # Close our current connection
        # self._conn.close()

        # # Open a new connection with the given autocommit status
        # self._connection_options["autocommit"] = mode
        # self._autocommit_status = mode

        # # Pass connection parameters as keyword arguments to the connection by unpacking the connection_options dict
        # self._conn = pymysql.connect(**self._connection_options)

        # # Check that we connected successfully
        # assert type(self._conn) is pymysql.connections.Connection
    
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """
        with self._conn.cursor() as cursor:
            try:
                cursor.execute(query)
                if all:
                    query_results = cursor.fetchall()
                else:
                    query_results = cursor.fetchone()

                return query_results
            finally:
                cursor.close()

    def execute_dict(self, query: str, params=None):
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        with self._conn.cursor() as cursor:
            try:
                cursor.execute(query)

                # Get a list of column names
                col_names: List[str] = [col[0] for col in cursor.description]

                rows: List[dict] = []
                if cursor.rowcount > 0:
                    for row in cursor:
                        # Map each column name to the corresponding value in each row
                        row_dict = {col_names[index]: row for index, row in enumerate(row)}
                        rows.append(row_dict)
                return col_names, rows
            except Exception as e:
                print(e)
            finally:
                cursor.close()

    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """
        return self.execute_query('SHOW DATABASES')
    
    def get_database_owner(self):
        """
        List the owner(s) of the current database
        """
        owner_query = 'SELECT CURRENT_USER();'
        result = self.execute_query(owner_query, all=True)[0][0]
        
        # Strip the hostname from the result
        return re.sub(r'@(\w)+', '', result)

    def close(self):
        """
        Closes this current connection.
        """
        self._conn.close()
        self._connection_closed = True