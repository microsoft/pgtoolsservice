# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Role(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Role':
        """
        Creates a Role object from the result of a role node query
        :param conn: Connection that executed the role node query
        :param kwargs: Row from a role node query
        Kwargs:
            name str: Name of the role
            oid int: Object ID of the role
            rolcanlogin bool: Whether or not the role can login
            rolsuper bool: Whether or not the role is a super user
        :return: A Role instance
        """
        role = cls(conn, kwargs['name'])

        # Define values from node query
        role._oid = kwargs['oid']
        role._can_login = kwargs['rolcanlogin']
        role._super = kwargs['rolsuper']

        return role

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes internal state of a Role object
        :param conn: Connection that executed the role node query
        :param name: Name of the role
        """
        super(Role, self).__init__(conn, name)

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

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT
