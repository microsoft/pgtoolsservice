# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating
import pgsmo.utils.querying as querying


class Tablespace(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Tablespace':
        """
        Creates a tablespace from a row of a nodes query result
        :param server: Server that owns the tablespace
        :param parent: Parent object of the tablespace. Must be None
        :param kwargs: Row from a node query for a list of
        :return: A Tablespace instance
        """
        tablespace = cls(server, kwargs['name'])

        tablespace._oid = kwargs['oid']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes internal state of a Role object
        :param server: Server that owns the tablespace
        :param name: Name of the role
        """
        super(Tablespace, self).__init__(server, None, name)

        # Declare basic properties
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def owner(self) -> Optional[int]:
        """Object ID of the user that owns the tablespace"""
        return self._owner

    @property
    def user(self):
        return self._full_properties.get("user", "")

    @property
    def location(self):
        return self._full_properties.get("location", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def options(self):
        return self._full_properties.get("options", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> str:
        return [cls.MACRO_ROOT]

    # SCRIPTING METHODS ####################################################

    def create_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve create scripts for a tablespace """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(connection, query_file, data)

    def delete_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve delete scripts for a table"""
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(connection, query_file, data)

    def update_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve update scripts for a table"""
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(connection, query_file, data, paths_to_add=self._macro_root())

    # HELPER METHODS #######################################################

    def _create_query_data(self):
        """ Returns the data needed for create query """
        return {"data": {
            "name": self.name,
            "spcuser": self.user,
            "spclocation": self.location
        }}

    def _delete_query_data(self):
        """ Returns the data needed for delete query """
        return {"tsname": self.name}

    def _update_query_data(self):
        """ Returns the data needed for update query """
        return {"data": {
            "name": self.name,
            "spcuser": self.user,
            "spclocation": self.location,
            "description": self.description,
            "spcoptions": self.options,
            "spcacl": self.acl
        }, "o_data": {
            "name": "",
            "spcuser": "",
            "description": ""
        }
        }
