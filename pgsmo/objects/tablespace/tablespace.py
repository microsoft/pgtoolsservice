# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Tablespace(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Tablespace':
        """
        Creates a tablespace from a row of a nodes query result
        :param conn: Connection to a server to use to lookup the information
        :param kwargs: Row from a node query for a list of
        :return: A Tablespace instance
        """
        tablespace = cls(conn, kwargs['name'])

        tablespace._oid = kwargs['oid']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes internal state of a Role object
        :param conn: Connection that executed the role node query
        :param name: Name of the role
        """
        super(Tablespace, self).__init__(conn, name)

        # Declare basic properties
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def owner(self) -> Optional[int]:
        """Object ID of the user that owns the tablespace"""
        return self._owner

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT
