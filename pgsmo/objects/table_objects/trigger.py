# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Trigger(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_trigger')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Trigger':
        """
        Creates a new Trigger object based on the results of a nodes query
        :param server: Server that owns the trigger
        :param parent: Parent object of the Trigger. Should be Table/View
        :param kwargs: Parameters for the trigger
        Kwargs:
            oid int: Object ID of the trigger
            name str: Name of the trigger
            is_enable_trigger bool: Whether or not the trigger is enabled
        :return: Instance of a Trigger
        """
        trigger = cls(server, parent, kwargs['name'])
        trigger._oid = kwargs['oid']

        # Basic properties
        trigger._is_enabled = kwargs['is_enable_trigger']

        return trigger

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        """
        Initializes a new instance of a trigger
        :param server: Connection the trigger belongs to
        :param parent: Parent object of the trigger. Should be Table/View
        :param name: Name of the trigger
        """
        super(Trigger, self).__init__(server, parent, name)

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

    def get_template_vars(self):
        template_vars = {'oid': self.oid}
        return template_vars