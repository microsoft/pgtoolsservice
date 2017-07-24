# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class Rule(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_rule')

    @classmethod
    def _from_node_query(cls, server: 's.Server', **kwargs) -> 'Rule':
        """
        Creates a new Rule object based on the results of a nodes query
        :param server: Server that owns the rule
        :param kwargs: Parameters for the rule
        Kwargs:
            name str: The name of the rule
            oid int: Object ID of the rule
        :return: Instance of the rule
        """
        idx = cls(server, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes a new instance of an rule
        :param server: Server that owns the rule
        :param name: Name of the rule
        """
        super(Rule, self).__init__(server, name)

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
