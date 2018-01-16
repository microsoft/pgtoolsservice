# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect
from pgsmo.objects.table_objects.column import Column

from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class ViewBase(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, ScriptableSelect):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')
    GLOBAL_MACRO_ROOT = templating.get_template_root(__file__, '../global_macros')

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
        view._schema = kwargs['schema']
        view._scid = kwargs['schemaoid']
        view._is_system = kwargs['is_system']

        return view

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableSelect.__init__(self, self._template_root(server), self._macro_root(), server.version)
        self._schema: str = None
        self._scid: int = None
        # Declare child items
        self._columns: NodeCollection[Column] = self._register_child_collection(Column)

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.scid,
            'did': self.parent.oid
        }
        return template_vars

    # -CHILD OBJECTS #######################################################
    @property
    def columns(self) -> NodeCollection[Column]:
        return self._columns

    # -FULL OBJECT PROPERTIES ##############################################

    @property
    def xmin(self):
        return self._full_properties.get("xmin", "")

    @property
    def relkind(self):
        return self._full_properties.get("relkind", "")

    @property
    def spcname(self):
        return self._full_properties.get("spcname", "")

    @property
    def spcoid(self):
        return self._full_properties.get("spcoid", "")

    @property
    def ispopulated(self):
        return self._full_properties.get("ispopulated", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def schema(self):
        return self._schema

    @property
    def definition(self):
        return self._full_properties.get("definition", "")

    @property
    def scid(self):
        return self._scid

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
        result = self._full_properties.get("check_option", " ")
        if result is not None:
            return result
        return "no"

    @property
    def security_barrier(self):
        result = self._full_properties.get("security_barrier", " ")
        if result is not None:
            return result

    # IMPLEMENTATION DETAILS ################################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT, cls.GLOBAL_MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "definition": self.definition,
                "check_option": self.check_option,
                "security_barrier": self.security_barrier,
                "owner": self.owner,
                "comment": self.comment,
            },
            "display_comments": True
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "name": self.name,
            "nspname": self.schema
        }

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        return {"data": {}}

    def _select_query_data(self) -> dict:
        """Provides data input for select script"""
        return {"data": {
            "name": self.name,
            "schema": self.schema,
            "columns": self.columns
        }}
