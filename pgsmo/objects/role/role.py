# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Role:
    @classmethod
    def get_roles_for_server(cls, conn: utils.querying.ConnectionWrapper) -> List['Role']:
        """
        Generates a list of roles for a given server. Intended to only be called by a Server object
        :param conn: Connection to use to look up the roles for the server
        :return: List of Role objects
        """
        sql = utils.templating.render_template(
            utils.templating.get_template_path(TEMPLATE_ROOT, 'nodes.sql', conn.version),
        )
        cols, rows = utils.querying.execute_dict(conn, sql)

        return [cls._from_node_query(conn, **row) for row in rows]

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Role':
        """
        Creates a Role object from the result of a role node query
        :param conn: Connection that executed the role node query
        :param kwargs: Row from a role node query
        :return: A Role instnace
        """
        role = cls()
        role._conn = conn

        # Define values from node query
        role._oid = kwargs.get('oid')
        role._name = kwargs.get('rolname')
        role._can_login = kwargs.get('rolcanlogin')
        role._super = kwargs.get('rolsuper')

        return role

    def __init__(self):
        """Initializes internal state of a Role object"""
        self._conn: Optional[utils.querying.ConnectionWrapper] = None

        # Declare basic properties
        self._oid: Optional[int] = None
        self._name: Optional[str] = None
        self._can_login: Optional[bool] = None
        self._super: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def can_login(self) -> Optional[bool]:
        """Whether or not the role can login to the server"""
        return self._can_login

    @property
    def name(self) -> Optional[str]:
        """Name of the role"""
        return self._name

    @property
    def oid(self) -> Optional[int]:
        """Object ID of the role"""
        return self._oid

    @property
    def super(self) -> Optional[bool]:
        """Whether or not the role is a super user"""
        return self._super
