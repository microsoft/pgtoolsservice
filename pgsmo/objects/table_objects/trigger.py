# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_trigger')


class Trigger(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, tid: int) -> List['Trigger']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, tid=tid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Trigger':
        """
        Creates a new Trigger object based on the results of a nodes query
        :param conn: Connection used to execute the nodes query
        :param kwargs: Parameters for the trigger
        Kwargs:
            oid int: Object ID of the trigger
            name str: Name of the trigger
            is_enable_trigger bool: Whether or not the trigger is enabled
        :return: Instance of a Trigger
        """
        trigger = cls(conn, kwargs['name'])
        trigger._oid = kwargs['oid']

        # Basic properties
        trigger._is_enabled = kwargs['is_enable_trigger']

        return trigger

    def __init__(self, conn: querying.ServerConnection, name: str):
        """
        Initializes a new instance of a trigger
        :param conn: Connection the trigger belongs to
        :param name: Name of the trigger
        """
        super(Trigger, self).__init__(conn, name)

        # Declare Trigger-specific basic properties
        self._is_enabled: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def is_enabled(self) -> Optional[bool]:
        """Whether or not the trigger is enabled"""
        return self._is_enabled
