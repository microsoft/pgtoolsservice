# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class Tablespace(NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Tablespace':
        """
        Creates a tablespace from a row of a nodes query result
        :param server: Server that owns the tablespace
        :param parent: Parent object of the tablespace. Must be None
        :param kwargs: Row from a node query for a list of
        :return: A Tablespace instance
        """
        tablespace = cls(server, parent, kwargs['name'])

        tablespace._oid = kwargs['oid']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self, server: 's.Server', parent: None, name: str):
        """
        Initializes internal state of a Role object
        :param server: Server that owns the tablespace
        :param parent: Parent object of the tablespace. Must be None
        :param name: Name of the role
        """
        if parent is not None:
            raise ValueError('Tablespace cannot have a parent node')

        super(Tablespace, self).__init__(server, parent, name)

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
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
