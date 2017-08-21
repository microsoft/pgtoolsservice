# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s        # noqa
import pgsmo.utils.templating as templating


class Role(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Role':
        """
        Creates a Role object from the result of a role node query
        :param server: Server that owns the role
        :param parent: Parent object of the role
        :param kwargs: Row from a role node query
        Kwargs:
            name str: Name of the role
            oid int: Object ID of the role
            rolcanlogin bool: Whether or not the role can login
            rolsuper bool: Whether or not the role is a super user
        :return: A Role instance
        """
        role = cls(server, kwargs['name'])

        # Define values from node query
        role._oid = kwargs['oid']
        role._can_login = kwargs['rolcanlogin']
        role._super = kwargs['rolsuper']

        return role

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes internal state of a Role object
        :param server: Server that owns the role
        :param name: Name of the role
        """
        super(Role, self).__init__(server, None, name)

        # Declare basic properties
        self._can_login: Optional[bool] = None
        self._super: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def can_login(self) -> Optional[bool]:
        """Whether or not the role can login to the server"""
        return self._can_login

    @property
    def super(self) -> Optional[bool]:
        """Whether or not the role is a super user"""
        return self._super

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def createdb(self):
        return self._full_properties.get("createdb", "")

    @property
    def createrole(self):
        return self._full_properties.get("createrole", "")

    @property
    def inherit(self):
        return self._full_properties.get("inherit", "")

    @property
    def replication(self):
        return self._full_properties.get("replication", "")

    @property
    def connlimit(self):
        return self._full_properties.get("connlimit", "")

    @property
    def validuntil(self):
        return self._full_properties.get("validuntil", "")

    @property
    def password(self):
        return self._full_properties.get("password", "")

    @property
    def catupdate(self):
        return self._full_properties.get("catupdate", "")

    @property
    def members(self):
        return self._full_properties.get("members", "")

    @property
    def admins(self):
        return self._full_properties.get("admins", "")

    @property
    def variables(self):
        return self._full_properties.get("variables", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def revoked_admins(self):
        return self._full_properties.get("revoked_admins", "")

    @property
    def revoked(self):
        return self._full_properties.get("revoked", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # SCRIPTING METHODS ####################################################

    def create_script(self) -> str:
        """ Function to retrieve create scripts for a role """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(query_file, data)

    def update_script(self) -> str:
        """ Function to retrieve create scripts for a role """
        data = self._update_query_data()
        query_file = "update.sql"
        filters = {'hasAny': templating.has_any}
        return self._get_template(query_file, data, filters_to_add=filters)

    # HELPER METHODS ##################################################################

    def _create_query_data(self):
        """ Gives the data object for create query """
        return {"data": {
            "rolcanlogin": self.can_login,
            "rolsuper": self.super,
            "rolcreatedb": self.createdb,
            "rolcreaterole": self.createrole,
            "rolinherit": self.inherit,
            "rolreplication": self.replication,
            "rolconnlimit": self.connlimit,
            "rolvaliduntil": self.validuntil,
            "rolpassword": self.password,
            "rolcatupdate": self.catupdate,
            "rolname": self.name,
            "members": self.members,
            "admins": self.admins,
            "variables": self.variables,
            "description": self.description
        }}

    def _update_query_data(self):
        """ Gives the data object for update query """
        return {
            "data": {
                "rolname": self.name,
                "rolcanlogin": self.can_login,
                "rolsuper": self.super,
                "rolcreatedb": self.createdb,
                "rolcreaterole": self.createrole,
                "rolinherit": self.inherit,
                "rolreplication": self.replication,
                "rolconnlimit": self.connlimit,
                "rolvaliduntil": self.validuntil,
                "rolpassword": self.password,
                "rolcatupdate": self.catupdate,
                "revoked_admins": self.revoked_admins,
                "revoked": self.revoked,
                "admins": self.admins,
                "members": self.members,
                "variables": self.variables,
                "description": self.description
            }, "rolCanLogin": self.can_login
        }
