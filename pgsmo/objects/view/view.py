# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.table_objects import Column, Rule, Trigger
import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s
import pgsmo.utils.templating as templating


class View(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param server: Server that owns the view
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(server, kwargs['name'])
        view._oid = kwargs['oid']

        return view

    def __init__(self, server: 's.Server', name: str):
        super(View, self).__init__(server, name)

        # Declare child items
        self._columns: node.NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._server, self)
        )
        self._rules: node.NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._server, self)
        )
        self._triggers: node.NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._server, self)
        )

    # PROPERTIES ###########################################################
    # -CHILD OBJECTS #######################################################
    @property
    def columns(self) -> node.NodeCollection[Column]:
        return self._columns

    @property
    def rules(self) -> node.NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> node.NodeCollection[Trigger]:
        return self._triggers

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
