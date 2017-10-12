# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Rule(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'rule')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Rule':
        """
        Creates a new Rule object based on the results of a nodes query
        :param server: Server that owns the rule
        :param parent: Parent object of the rule. Should be Table/View
        :param kwargs: Parameters for the rule
        Kwargs:
            name str: The name of the rule
            oid int: Object ID of the rule
        :return: Instance of the rule
        """
        idx = cls(server, parent, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes a new instance of an rule
        :param server: Server that owns the rule
        :param parent: Parent object of the rule. Should be Table/View
        :param name: Name of the rule
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

    # PROPERTIES ###########################################################

    @property
    def view(self):
        return self._full_properties["view"]

    @property
    def event(self):
        return self._full_properties["event"]

    @property
    def condition(self):
        return self._full_properties["condition"]

    @property
    def do_instead(self):
        return self._full_properties["do_instead"]

    @property
    def statements(self):
        return self._full_properties["statements"]

    @property
    def comment(self):
        return self._full_properties["comment"]

    @property
    def display_comments(self):
        return self._full_properties["display_comments"]

    @property
    def rid(self):
        return self._full_properties["rid"]

    @property
    def rulename(self):
        return self._full_properties["rulename"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.schema,
                "view": self.view,
                "event": self.event,
                "condition": self.condition,
                "do_instead": self.do_instead,
                "statements": self.statements,
                "comment": self.comment
            },
            "display_comments": self.display_comments
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "rid": self.rid,
            "rulename": self.rulename,
            "relname": self.parent.name,
            "nspname": self.parent.schema
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "event": self.event,
                "do_instead": self.do_instead,
                "condition": self.condition,
                "statements": self.statements,
                "comment": self.comment
            },
            "o_data": {
                "name": "",
                "schema": "",
                "view": "",
                "condition": "",
                "do_instead": "",
                "statements": ""
            }
        }
