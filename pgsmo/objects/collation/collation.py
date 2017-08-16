# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating
import pgsmo.utils.querying as querying


class Collation(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Collation':
        """
        Creates a Collation object from the results of a node query
        :param server: Server that owns the collation
        :param parent: Parent object of this object
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the collation
            name str: Name of the collation
        :return: A Collation instance
        """
        collation = cls(server, parent, kwargs['name'])
        collation._oid = kwargs['oid']

        return collation

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(Collation, self).__init__(server, parent, name)

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # -BASIC PROPERTIES ####################################################
    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def schema(self):
        return self._full_properties.get("schema")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def lc_collate(self):
        return self._full_properties.get("lc_collate", "")

    @property
    def lc_type(self):
        return self._full_properties.get("lc_type", "")

    @property
    def locale(self):
        return self._full_properties.get("locale", "")

    @property
    def copy_collation(self):
        return self._full_properties.get("copy_collation", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    # SCRIPTING METHODS ##############################################################
    def create_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve create scripts for a collation """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(connection, query_file, data)

    def delete_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve delete scripts for a collation"""
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(connection, query_file, data)

    def update_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve update scripts for a collation"""
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(connection, query_file, data)

    # HELPER METHODS ####################################################################
    # QUERY DATA BUILDING METHODS #######################################################

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        data = {"data": {
            "name": self.name,
            "pronamespace": self.parent.name,
            "owner": self.owner,
            "schema": self.schema,
            "description": self.description,
            "lc_collate": self.lc_collate,
            "lc_type": self.lc_type,
            "locale": self.locale,
            "copy_collation": self.copy_collation
        }}
        return data

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        data = {
            "data": {
                "name": self.name,
                "schema": self.parent.name
            }, "cascade": self.cascade
        }
        return data

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        data = {"data": {
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "schema": self.schema
        },
            "o_data": {
                "name": "",
                "owner": "",
                "description": "",
                "schema": ""
            }
        }
        return data
