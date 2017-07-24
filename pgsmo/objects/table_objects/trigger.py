# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class Trigger(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_trigger')

    @classmethod
    def _from_node_query(cls, server: 's.Server', **kwargs) -> 'Trigger':
        """
        Creates a new Trigger object based on the results of a nodes query
        :param server: Server that owns the trigger
        :param kwargs: Parameters for the trigger
        Kwargs:
            oid int: Object ID of the trigger
            name str: Name of the trigger
            is_enable_trigger bool: Whether or not the trigger is enabled
        :return: Instance of a Trigger
        """
        trigger = cls(server, kwargs['name'])
        trigger._oid = kwargs['oid']

        # Basic properties
        trigger._is_enabled = kwargs['is_enable_trigger']

        return trigger

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes a new instance of a trigger
        :param server: Connection the trigger belongs to
        :param name: Name of the trigger
        """
        super(Trigger, self).__init__(server, name)

        # Declare Trigger-specific basic properties
        self._is_enabled: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def is_enabled(self) -> Optional[bool]:
        """Whether or not the trigger is enabled"""
        return self._is_enabled

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
