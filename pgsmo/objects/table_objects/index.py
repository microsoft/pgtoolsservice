# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class Index(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_index')

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

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT
