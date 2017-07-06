# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Index(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, tid: int) -> List['Index']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, tid=tid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Index':
        """
        Creates a new Index object based on the results of a nodes query
        :param conn: Connection used to execute the nodes query
        :param kwargs: Parameters for the index
        Kwargs:
            name str: The name of the index
            oid int: Object ID of the index
        :return: Instance of the Index
        """
        idx = cls(conn, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes a new instance of an Index
        :param conn: Connection to the server/database that this object will belong to
        :param name: Name of the index
        """
        super(Index, self).__init__(conn, name)

    # PROPERTIES ###########################################################
