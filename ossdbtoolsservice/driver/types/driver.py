# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Tuple
from abc import ABC, abstractmethod


class ServerConnection(ABC):
    """Abstract base class that outlines methods and properties that connections must implement"""

    # PROPERTIES ###########################################################
    @property
    @abstractmethod
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""

    @property
    @abstractmethod
    def host_name(self) -> str:
        """Returns the hostname for the current connection"""

    @property
    @abstractmethod
    def port(self) -> int:
        """Returns the port number used for the current connection"""

    @property
    @abstractmethod
    def user_name(self) -> str:
        """Returns the user name used for the current connection"""

    @property
    @abstractmethod
    def database_name(self) -> str:
        """Return the name of the current connection's database"""

    @property
    @abstractmethod
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""

    @property
    @abstractmethod
    def server_type(self) -> str:
        """Returns the server type/provider"""

    @property
    @abstractmethod
    def connection_options(self) -> dict:
        """ Returns the options used to create the current connection to the server """

    @property
    @abstractmethod
    def default_database(self) -> str:
        """Returns the default database if no other database is specified"""

    @property
    @abstractmethod
    def database_error(self) -> Exception:
        """ Returns the type of database error this connection throws"""

    @property
    @abstractmethod
    def transaction_in_error(self) -> bool:
        """Returns bool indicating if transaction is in error"""
                              
    @property
    @abstractmethod
    def query_canceled_error(self) -> Exception:
        """Returns driver query canceled error"""
                         
    @property
    @abstractmethod
    def cancellation_query(self) -> str:
        """
        Returns a SQL command to end the current query execution process
        """

    @property
    @abstractmethod
    def connection(self) -> 'connection':
        """
        Returns the underlying connection
        """

    @property
    @abstractmethod
    def open(self) -> bool:
        """
        Returns bool indicating if connection is open
        """

    # METHODS ##############################################################

    @autocommit.setter
    @abstractmethod
    def autocommit(self, mode: bool):
        """
        Sets the connection's autocommit setting to the specified mode
        :param mode: True or False
        """

    @abstractmethod
    def commit(self):
        """
        Commits the current transaction
        """

    @abstractmethod
    def cursor(self, **kwargs):
        """
        Returns a cursor for the current connection
        """

    @abstractmethod
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """

    @abstractmethod
    def execute_dict(self, query: str, params=None):
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """

    @abstractmethod
    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """

    @abstractmethod
    def get_database_owner(self):
        """
        List the owner(s) of the current database
        """

    @abstractmethod
    def get_database_size(self, dbname: str):
        """
        Gets the size of a particular database in MB
        """
        pass

    @abstractmethod
    def get_error_message(self, error) -> str:
        """
        Get the message from database error instance
        """
        pass

    @abstractmethod
    def close(self):
        """
        Closes this current connection.
        """
