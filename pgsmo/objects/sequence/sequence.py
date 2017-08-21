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

    # SCRIPTING METHODS ####################################################

    def create_script(self) -> str:
        """ Function to retrieve create scripts for a sequence """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(query_file, data)

    def update_script(self) -> str:
        """ Function to retrieve create scripts for a sequence """
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(query_file, data)

    def delete_script(self) -> str:
        """ Function to retrieve delete scripts for a sequence"""
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(query_file, data)

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
        }, "cascade": self.cascade
        }
