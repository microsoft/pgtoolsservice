# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Index(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_index')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Index':
        """
        Creates a new Index object based on the results of a nodes query
        :param server: Server that owns the index
        :param parent: Parent object of the Index. Should be Table/View
        :param kwargs: Parameters for the index
        Kwargs:
            name str: The name of the index
            oid int: Object ID of the index
        :return: Instance of the Index
        """
        idx = cls(server, parent, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        """
        Initializes a new instance of an Index
        :param server: Server that owns the index
        :param parent: Parent object of the index. Should be Table/View
        :param name: Name of the index
        """
        super(Index, self).__init__(server, parent, name)

        # Full Object Properties
        self._is_clustered: Optional[bool] = None
        self._is_primary: Optional[bool] = None
        self._is_unique: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def is_clustered(self) -> Optional[bool]:
        return self._full_properties['indisclustered']

    @property
    def is_primary(self) -> Optional[bool]:
        return self._full_properties['indisprimary']

    @property
    def is_unique(self) -> Optional[bool]:
        return self._full_properties['indisunique']

    @property
    def extended_vars(self):
        return {'tid': self.parent.oid}

    # IMPLEMENTATION DETAILS ###############################################
    @property
    def extended_vars(self):
        return {
            'tid': self.parent.oid,                 # Table/view OID
            'did': self.parent.parent.parent.oid    # Database OID
        }

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
