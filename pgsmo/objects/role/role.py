# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class Role(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject,  **kwargs) -> 'Role':
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
        role = cls(server, parent, kwargs['name'])

        # Define values from node query
        role._oid = kwargs['oid']
        role._can_login = kwargs['rolcanlogin']
        role._super = kwargs['rolsuper']

        return role

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes internal state of a Role object
        :param server: Server that owns the role
        :param parent: Parent object of the role, should always be None
        :param name: Name of the role
        """
        if parent is not None:
            raise ValueError('Role object cannot have parent object')

        super(Role, self).__init__(server, parent, name)

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
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
