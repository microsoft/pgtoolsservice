# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.table_objects.column import Column
from pgsmo.objects.table_objects.rule import Rule
from pgsmo.objects.table_objects.trigger import Trigger
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class View(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param server: Server that owns the view
        :param parent: Object that is the parent of the view. Should be a Schema
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(server, parent, kwargs['name'])
        view._oid = kwargs['oid']

        return view

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare child items
        self._columns: NodeCollection[Column] = self._register_child_collection(Column)
        self._rules: NodeCollection[Rule] = self._register_child_collection(Rule)
        self._triggers: NodeCollection[Trigger] = self._register_child_collection(Trigger)

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.parent.oid
        }
        return template_vars

    # -CHILD OBJECTS #######################################################
    @property
    def columns(self) -> NodeCollection[Column]:
        return self._columns

    @property
    def rules(self) -> NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> NodeCollection[Trigger]:
        return self._triggers

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def schema(self):
        return self._full_properties.get("schema", "")

    @property
    def definition(self):
        return self._full_properties.get("definition", "")

    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def comment(self):
        return self._full_properties.get("comment", "")

    @property
    def nspname(self):
        return self._full_properties.get("nspname", "")

    @property
    def check_option(self):
        return self._full_properties.get("check_option", "")

    @property
    def security_barrier(self):
        return self._full_properties.get("security_barrier", "")

    # IMPLEMENTATION DETAILS ################################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {"data": {
            "name": self.name,
            "schema": self.parent.name,
            "definition": self.definition,
            "check_option": self.check_option,
            "security_barrier": self.security_barrier
        }}

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "vid": self._oid,
            "name": self.name,
            "nspname": self.nspname
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {"data": {}}
