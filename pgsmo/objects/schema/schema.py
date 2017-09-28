# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Schema(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Schema':
        """
        Creates an instance of a schema object from the results of a nodes query
        :param server: Server that owns the schema
        :param parent: Parent object of the schema. Should be a Database
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the schema
            oid int: Object ID of the schema
            can_create bool: Whether or not the schema can be created by the current user
            has_usage bool: Whether or not the schema can be used(?)
        :return:
        """
        schema = cls(server, parent, kwargs['name'])
        schema._oid = kwargs['oid']
        schema._can_create = kwargs['can_create']
        schema._has_usage = kwargs['has_usage']

        return schema

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare the optional parameters
        self._can_create: Optional[bool] = None
        self._has_usage: Optional[bool] = None

    # PROPERTIES ###########################################################
    @property
    def can_create(self) -> Optional[bool]:
        return self._can_create

    @property
    def has_usage(self) -> Optional[bool]:
        return self._has_usage

    # -CHILD OBJECTS #######################################################
    @property
    def collations(self) -> NodeCollection:
        return [collation for collation in self.parent.collations if collation.scid == self.oid]

    @property
    def datatypes(self) -> NodeCollection:
        return [datatype for datatype in self.parent.datatypes if datatype.scid == self.oid]

    @property
    def functions(self) -> NodeCollection:
        return [function for function in self.parent.functions if function.scid == self.oid]

    @property
    def sequences(self) -> NodeCollection:
        return [sequence for sequence in self.parent.sequences if sequence.scid == self.oid]

    @property
    def tables(self) -> NodeCollection:
        return [table for table in self.parent.tables if table.scid == self.oid]

    @property
    def trigger_functions(self) -> NodeCollection:
        return [trigger for trigger in self.parent.trigger_functions if trigger.scid == self.oid]

    @property
    def views(self) -> NodeCollection:
        return [view for view in self.parent.views if view.scid == self.oid]

    @property
    def namespaceowner(self):
        return self._full_properties.get("namespaceowner", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def nspacl(self):
        return self._full_properties.get("nspacl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    @property
    def defacl(self):
        return self._full_properties.get("defacl", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return path.join(cls.TEMPLATE_ROOT, server.server_type)

    def _create_query_data(self) -> dict:
        """ Function that returns data for create script """
        return {"data": {
            "name": self.name,
            "namespaceowner": self.namespaceowner,
            "description": self.description,
            "nspacl": self.nspacl,
            "seclabels": self.seclabels
        }}

    def _delete_query_data(self) -> dict:
        """ Function that returns data for delete script """
        return {
            "name": self.name,
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "namespaceowner": self.namespaceowner,
                "description": self.description,
                "nspacl": self.nspacl,
                "defacl": self.defacl,
                "seclabels": self.seclabels
            }, "o_data": {
                "name": "",
                "namespaceowner": "",
                "description": ""
            }
        }
