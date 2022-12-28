# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing the logic to set up database connection for integration tests"""

from abc import abstractclassmethod
from typing import List
import mysql


class IConnection():

    """
    Opens the connection for the list of connection details dict provided

    :params connection_details_list: list of connection details dict
    """
    @abstractclassmethod
    def open_connections(cls, connection_details_list):
        pass

    """
    Fetch the list of connections opened
    """
    @abstractclassmethod
    def get_connections(cls):
        pass

    """
    Get the server version of the connection at index

    :params index: index of connection to be fetched
    """
    @abstractclassmethod
    def get_connection_server_version(cls, index):
        pass


class MySQLConnection:

    _connections: List[mysql.connector.MySQLConnection] = []

    @classmethod
    def open_connections(cls, connection_details_list):
        cls._connections = []
        for config_dict in connection_details_list:
            connection = mysql.connector.connect(**config_dict)
            cls._connections.append(connection)
            connection.autocommit = True

    @classmethod
    def get_connections(cls):
        return cls._connections

    @classmethod
    def get_connection_server_version(cls, index):
        return cls._connections[index].server_version
