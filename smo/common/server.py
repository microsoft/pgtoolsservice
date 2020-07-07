# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, List, Mapping, Optional, Tuple, Callable      # noqa
from abc import ABC, abstractmethod

from ossdbtoolsservice.driver import ServerConnection
from smo.common.node_object import NodeObject, NodeCollection

class Server(ABC):
    """Abstract base class that outlines methods and properties that servers must implement"""
     # PROPERTIES ###########################################################
    @property
    @abstractmethod
    def connection(self) -> ServerConnection:
        """Connection to the server/db that this object will use"""
        pass

    @property
    @abstractmethod
    def db_connection_callback(self):
        """Connection to the server/db that this object will use"""
        pass

    @property
    @abstractmethod
    def host(self) -> str:
        """Hostname of the server"""
        pass

    @property
    @abstractmethod
    def in_recovery(self) -> Optional[bool]:
        """Whether or not the server is in recovery mode. If None, value was not loaded from server"""
        pass

    @property
    @abstractmethod
    def maintenance_db_name(self) -> str:
        """Name of the database this server's connection is connected to"""
        pass

    @property
    @abstractmethod
    def port(self) -> int:
        """Port number of the server"""
        pass

    @property
    @abstractmethod
    def version(self) -> Tuple[int, int, int]:
        """Tuple representing the server version: (major, minor, patch)"""
        pass

    @property
    @abstractmethod
    def urn_base(self) -> str:
        """Base of a URN for objects in the tree"""
        pass

    @property
    @abstractmethod
    def wal_paused(self) -> Optional[bool]:
        """Whether or not the Write-Ahead Log (WAL) is paused. If None, value was not loaded from server"""
        pass
    
    # -CHILD OBJECTS #######################################################
    @property
    @abstractmethod
    def databases(self) -> NodeCollection['Database']:
        """Databases that belong to the server"""
        pass

    @property
    @abstractmethod
    def maintenance_db(self) -> 'Database':
        """Database that this server's connection is connected to"""
        pass

    @property
    @abstractmethod
    def roles(self) -> NodeCollection['Role']:
        """Roles that belong to the server"""
        pass

    @property
    @abstractmethod
    def tablespaces(self) -> NodeCollection['Tablespace']:
        """Tablespaces defined for the server"""
        pass

    @property
    @abstractmethod
    def search_path(self) -> NodeCollection[str]:
        """
        The search_path for the current role. Defined at the server level as it's a global property,
        and as a collection as it is a list of schema names
        """
        pass

    # METHODS ##############################################################
    @abstractmethod
    def get_object_by_urn(self, urn: str) -> NodeObject:
        pass

    @abstractmethod
    def refresh(self) -> None:
        pass
    
    @abstractmethod
    def find_schema(self, metadata):
        """ Find the schema in the server to script as """
        pass

    @abstractmethod
    def find_table(self, metadata):
        """ Find the table in the server to script as """
        pass

    @abstractmethod
    def find_function(self, metadata):
        """ Find the function in the server to script as """
        pass

    @abstractmethod
    def find_database(self, metadata):
        """ Find a database in the server """
        pass

    @abstractmethod
    def find_view(self, metadata):
        """ Find a view in the server """
        pass

    @abstractmethod
    def find_materialized_view(self, metadata):
        """ Find a view in the server """
        pass

    @abstractmethod
    def find_role(self, metadata):
        """ Find a role in the server """
        pass

    @abstractmethod
    def find_sequence(self, metadata):
        """ Find a sequence in the server """
        pass

    @abstractmethod
    def find_datatype(self, metadata):
        """ Find a datatype in the server """
        pass

    @abstractmethod
    def find_schema_child_object(self, prop_name: str, metadata):
        """
        Find an object that is a child of a schema object.
        :param prop_name: name of the property used to query for objects
        of this type on the schema
        :param metadata: metadata including object name and schema name
        """
        pass

    @abstractmethod
    def get_object(self, object_type: str, metadata):
        """ Retrieve a given object """
        pass
