# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Rule(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, tid: int) -> List['Rule']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, tid=tid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Rule':
        """
        Creates a new Rule object based on the results of a nodes query
        :param conn: Connection used to execute the nodes query
        :param kwargs: Parameters for the rule
        Kwargs:
            name str: The name of the rule
            oid int: Object ID of the rule
        :return: Instance of the rule
        """
        idx = cls(conn, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes a new instance of an rule
        :param conn: Connection to the server/database that this object will belong to
        :param name: Name of the rule
        """
        super(Rule, self).__init__(conn, name)

    # PROPERTIES ###########################################################
