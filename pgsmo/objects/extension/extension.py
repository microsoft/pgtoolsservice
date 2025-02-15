# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path

import smo.utils.templating as templating
from pgsmo.objects.server import server as s  # noqa
from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete


class Extension(NodeObject, ScriptableCreate, ScriptableDelete):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "templates")
    MACRO_ROOT = templating.get_template_root(__file__, "macros")
    GLOBAL_MACRO_ROOT = templating.get_template_root(__file__, "../global_macros")

    @classmethod
    def _from_node_query(
        cls, server: "s.Server", parent: NodeObject, **kwargs
    ) -> "Extension":
        """
        Creates a table instance from the results of a node query
        :param server: Server that owns the table
        :param parent: Parent object of the table. Should be a Schema
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the table
            name str: Name of the table
        :return: A table instance
        """
        extension = cls(server, parent, kwargs["name"])
        extension._oid = kwargs["oid"]
        extension._schema = kwargs["schema"]
        extension._scid = kwargs["schemaoid"]
        extension._is_system = kwargs["is_system"]

        return extension

    def __init__(self, server: "s.Server", parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )
        ScriptableDelete.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )

        self._schema: str = None
        self._scid: int = None

    # PROPERTIES ###########################################################
    @property
    def schema(self):
        return self._schema

    @property
    def scid(self):
        return self._scid

    @property
    def extended_vars(self):
        template_vars = {"scid": self.scid, "did": self.parent.oid}
        return template_vars

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def relocatable(self):
        return self._full_properties.get("relocatable", "")

    @property
    def version(self):
        return self._full_properties.get("version", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> list[str]:
        return [cls.MACRO_ROOT, cls.GLOBAL_MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return path.join(cls.TEMPLATE_ROOT, server.server_type)

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {"data": {"name": self.name, "schema": self.schema}}

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {
            "data": {"name": self.name, "schema": self.schema},
        }
