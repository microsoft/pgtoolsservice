# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# from abc import ABC, abstractmethod
# from typing import Dict, List, Mapping, Optional, Tuple, Callable      # noqa
# from pgsqltoolsservice.driver import ServerConnection

# class Server(ABC):

#     # CONSTRUCTOR ##########################################################
#     def __init__(self, conn: ServerConnection, db_connection_callback: Callable[[str], ServerConnection] = None):
#         """
#         Initializes a server object using the provided connection
#         :param conn: a connection object
#         """
#         pass

#     # PROPERTIES ###########################################################
#     @property
#     @abstractmethod
#     def connection(self) -> ServerConnection:
#         """Connection to the server/db that this object will use"""
#         pass

#     @property
#     @abstractmethod
#     def db_connection_callback(self):
#         """Connection to the server/db that this object will use"""
#         pass

#     @property
#     @abstractmethod
#     def host(self) -> str:
#         """Hostname of the server"""
#         pass

#     @property
#     @abstractmethod
#     def maintenance_db_name(self) -> str:
#         """Name of the database this server's connection is connected to"""
#         pass

#     @property
#     @abstractmethod
#     def port(self) -> int:
#         """Port number of the server"""
#         pass

#     @property
#     @abstractmethod
#     def version(self) -> Tuple[int, int, int]:
#         """Tuple representing the server version: (major, minor, patch)"""
#         pass

#     @property
#     @abstractmethod
#     def server_type(self) -> str:
#         """Server type for distinguishing between different server types e.g MySQL vs MariaDB"""
#         pass
    
#     # METHODS ##############################################################
    
#     @abstractmethod
#     def refresh(self) -> None:
#         # Refresh all child objects in tree
#         pass
    


    
    

    
