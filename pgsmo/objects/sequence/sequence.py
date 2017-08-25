# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Sequence(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

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
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

    # PROPERTIES ###########################################################
    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def schema(self):
        return self._full_properties.get("schema", "")

    @property
    def cycled(self):
        return self._full_properties.get("cycled", "")

    @property
    def increment(self):
        return self._full_properties.get("increment", "")

    @property
    def start(self):
        return self._full_properties.get("start", "")

    @property
    def current_value(self):
        return self._full_properties.get("current_value", "")

    @property
    def minimum(self):
        return self._full_properties.get("minimum", "")

    @property
    def maximum(self):
        return self._full_properties.get("maximum", "")

    @property
    def cache(self):
        return self._full_properties.get("cache", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    @property
    def seqowner(self):
        return self._full_properties.get("seqowner", "")

    @property
    def comment(self):
        return self._full_properties.get("comment", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # HELPER METHODS ##################################################################

    def _create_query_data(self):
        """ Gives the data object for create query """
        return {"data": {
            "schema": self.schema,
            "name": self.name,
            "cycled": self.cycled,
            "increment": self.increment,
            "start": self.start,
            "current_value": self.current_value,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "cache": self.cache
        }}

    def _update_query_data(self):
        """ Gives the data object for update query """
        return {
            "data": {
                "schema": self.schema,
                "name": self.name,
                "cycled": self.cycled,
                "increment": self.increment,
                "start": self.start,
                "current_value": self.current_value,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "cache": self.cache
            },
            "o_data": {
                "schema": self.schema,
                "name": self.name,
                "seqowner": self.seqowner,
                "comment": self.comment
            }
        }

    def _delete_query_data(self):
        """ Gives the data object for update query """
        return {
            "data": {
                "schema": self.schema,
                "name": self.name,
                "cycled": self.cycled,
                "increment": self.increment,
                "start": self.start,
                "current_value": self.current_value,
                "minimum": self.minimum,
                "maximum": self.maximum,
                "cache": self.cache
            },
            "cascade": self.cascade
        }
