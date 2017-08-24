# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Tablespace(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Tablespace':
        """
        Creates a tablespace from a row of a nodes query result
        :param server: Server that owns the tablespace
        :param parent: Parent object of the tablespace. Must be None
        :param kwargs: Row from a node query for a list of
        :return: A Tablespace instance
        """
        tablespace = cls(server, kwargs['name'])

        tablespace._oid = kwargs['oid']
        tablespace._owner = kwargs['owner']

        return tablespace

    def __init__(self, server: 's.Server', name: str):
        """
        Initializes internal state of a Role object
        """
        NodeObject.__init__(self, server, None, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare basic properties
        self._owner: Optional[int] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def owner(self) -> Optional[int]:
        """Object ID of the user that owns the tablespace"""
        return self._owner

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def user(self):
        return self._full_properties.get("user", "")

    @property
    def location(self):
        return self._full_properties.get("location", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def options(self):
        return self._full_properties.get("options", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self):
        """ Returns the data needed for create query """
        return {"data": {
            "name": self.name,
            "spcuser": self.user,
            "spclocation": self.location
        }}

    def _delete_query_data(self):
        """ Returns the data needed for delete query """
        return {"tsname": self.name}

    def _update_query_data(self):
        """ Returns the data needed for update query """
        return {
            "data": {
                "name": self.name,
                "spcuser": self.user,
                "spclocation": self.location,
                "description": self.description,
                "spcoptions": self.options,
                "spcacl": self.acl
            },
            "o_data": {
                "name": "",
                "spcuser": "",
                "description": ""
            }
        }
