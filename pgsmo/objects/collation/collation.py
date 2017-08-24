# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Collation(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Collation':
        """
        Creates a Collation object from the results of a node query
        :param server: Server that owns the collation
        :param parent: Parent object of this object
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the collation
            name str: Name of the collation
        :return: A Collation instance
        """
        collation = cls(server, parent, kwargs['name'])
        collation._oid = kwargs['oid']

        return collation

    def __init__(self,  server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def schema(self):
        return self._full_properties.get("schema")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def lc_collate(self):
        return self._full_properties.get("lc_collate", "")

    @property
    def lc_type(self):
        return self._full_properties.get("lc_type", "")

    @property
    def locale(self):
        return self._full_properties.get("locale", "")

    @property
    def copy_collation(self):
        return self._full_properties.get("copy_collation", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {"data": {
            "name": self.name,
            "pronamespace": self.parent.name,
            "owner": self.owner,
            "schema": self.schema,
            "description": self.description,
            "lc_collate": self.lc_collate,
            "lc_type": self.lc_type,
            "locale": self.locale,
            "copy_collation": self.copy_collation
        }}

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.name
            }, "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {
            "data": {
                "name": self.name,
                "owner": self.owner,
                "description": self.description,
                "schema": self.schema
            },
            "o_data": {
                "name": "",
                "owner": "",
                "description": "",
                "schema": ""
            }
        }
