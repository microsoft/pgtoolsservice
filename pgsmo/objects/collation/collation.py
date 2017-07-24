# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class Collation(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', **kwargs) -> 'Collation':
        """
        Creates a Collation object from the results of a node query
        :param server: Server that owns the collation
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the collation
            name str: Name of the collation
        :return: A Collation instance
        """
        collation = cls(server, kwargs['name'])
        collation._oid = kwargs['oid']

        return collation

    def __init__(self, server: 's.Server', name: str):
        super(Collation, self).__init__(server, name)

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
