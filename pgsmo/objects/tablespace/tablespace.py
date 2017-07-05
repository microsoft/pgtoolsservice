# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

from pgsmo.objects.node_object import NodeObject, get_nodes
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Tablespace(NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ServerConnection) -> List['Tablespace']:
        """
        Creates a list of tablespaces that belong to the server. Intended to be called by Server class
        :param conn: Connection to a server to use to lookup the information
        :return: List of tablespaces for the given server
        """
        return get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ServerConnection, **kwargs) -> 'Tablespace':
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

    def __init__(self, conn: utils.querying.ServerConnection, name: str):
        """
        Initializes internal state of a Role object
        :param conn: Connection that executed the role node query
        :param name: Name of the role
        """
        super(Tablespace, self).__init__(conn, name)

        # Declare basic properties
        self._oid: Optional[int] = None
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def owner(self) -> Optional[int]:
        """Object ID of the user that owns the tablespace"""
        return self._owner
