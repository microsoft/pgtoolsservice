# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

from pgsmo.objects.node_object import NodeObject, get_nodes
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Role(NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper) -> List['Role']:
        """
        Generates a list of roles for a given server. Intended to only be called by a Server object
        :param conn: Connection to use to look up the roles for the server
        :return: List of Role objects
        """
        return get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Role':
        """
        Creates a Role object from the result of a role node query
        :param conn: Connection that executed the role node query
        :param kwargs: Row from a role node query
        :return: A Role instnace
        """
        role = cls(conn, kwargs['rolname'])

        # Define values from node query
        role._oid = kwargs['oid']
        role._can_login = kwargs['rolcanlogin']
        role._super = kwargs['rolsuper']

        return role

    def __init__(self, conn: utils.querying.ConnectionWrapper, name: str):
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
