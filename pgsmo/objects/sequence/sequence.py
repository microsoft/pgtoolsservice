# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Sequence(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Sequence':
        """
        Creates a Sequence object from the result of a sequence node query
        :param server: Server that owns the sequence
        :param parent: Parent object of the sequence
        :param kwargs: Row from a sequence node query
        Kwargs:
            oid int: Object ID of the sequence
            name str: Name of the sequence
        :return: A Sequence instance
        """
        seq = cls(server, parent, kwargs['name'])
        seq._oid = kwargs['oid']

        return seq

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        super(Sequence, self).__init__(server, parent, name)

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def get_template_vars(self):
        template_vars = {'oid': self.oid}
        return template_vars
