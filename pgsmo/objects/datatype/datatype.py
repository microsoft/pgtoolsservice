# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Any, Optional

import smo.utils.templating as templating
from pgsmo.objects.server import server as s  # noqa
from smo.common.node_object import NodeLazyPropertyCollection, NodeObject  # noqa
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate

TEMPLATE_ROOT = templating.get_template_root(__file__, "templates")
MACRO_ROOT = templating.get_template_root(__file__, "macros")
GLOBAL_MACRO_ROOT = templating.get_template_root(__file__, "../global_macros")


class DataType(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    """Represents a data type"""

    @classmethod
    def _from_node_query(cls, server: "s.Server", parent: NodeObject, **kwargs) -> "DataType":
        """
        Creates a Type object from the result of a DataType node query
        :param server: Server that owns the DataType
        :param parent: Parent object of the DataType
        :param kwargs: Row from a DataType node query
        Kwargs:
            name str: Name of the DataType
            oid int: Object ID of the DataType
        :return: A DataType instance
        """
        datatype = cls(server, parent, kwargs["name"])

        # Define values from node query
        datatype._oid = kwargs["oid"]
        datatype._schema = kwargs["schema"]
        datatype._scid = kwargs["schemaoid"]
        datatype._is_system = kwargs["is_system"]

        return datatype

    def __init__(self, server: "s.Server", parent: NodeObject, name: str):
        """
        Initializes internal state of a DataType object
        :param server: Server that owns the role
        :param name: Name of the role
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(
            self, self._template_root(self.server), self._macro_root(), self.server.version
        )
        ScriptableDelete.__init__(
            self, self._template_root(self.server), self._macro_root(), self.server.version
        )
        ScriptableUpdate.__init__(
            self, self._template_root(self.server), self._macro_root(), self.server.version
        )
        self._schema: str = None
        self._scid: int = None
        self._additional_properties: NodeLazyPropertyCollection = (
            self._register_property_collection(self._additional_property_generator)
        )

    # PROPERTIES ###########################################################
    @property
    def schema(self):
        return self._schema

    @property
    def scid(self):
        return self._scid

    @property
    def is_collatable(self) -> Optional[bool]:
        """Whether or not the DataType is collatable"""
        return self._full_properties.get("is_collatable", "")

    # TODO acl seems to be handled by separate query so skip for now
    # @property
    # def typeacl(self):
    #     return self._full_properties.get("type_acl", "")

    @property
    def alias(self):
        return self._full_properties.get("alias", "")

    @property
    def typeowner(self):
        return self._full_properties.get("typeowner", "")

    @property
    def element(self):
        return self._full_properties.get("element", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def is_sys_type(self):
        return self._full_properties.get("is_sys_type", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def typtype(self) -> str:
        return self._full_properties.get("typtype", "")

    @property
    def typname(self):
        return self._additional_properties.get("typname", "")

    @property
    def collname(self):
        return self._additional_properties.get("collname", "")

    @property
    def opcname(self):
        return self._additional_properties.get("opcname", "")

    @property
    def rngsubdiff(self):
        return self._additional_properties.get("rngsubdiff", "")

    @property
    def rngcanonical(self):
        return self._additional_properties.get("rngcanonical", "")

    @property
    def composite(self) -> Optional[list[Any]]:
        if self.typtype != "c":
            return None
        composite = []
        # TODO support composite, which is a complex property
        return composite

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> list[str]:
        return [MACRO_ROOT, GLOBAL_MACRO_ROOT]

    def _create_query_data(self):
        """Gives the data object for create query"""
        # TODO support composite data type properties
        # TODO support enum value
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "typtype": self.typtype,
                "collname": self.collname,
                "opcname": self.opcname,
                "rngcanonical": self.rngcanonical,
                "rngsubdiff": self.rngsubdiff,
                "description": self.description,
                "composite": self.composite,
            }
        }

    def _update_query_data(self):
        """Gives the data object for update query"""
        return {
            "data": {
                "name": self.name,
                "typeowner": self.typeowner,
                "description": self.description,
                "schema": self.schema,
            },
            # This will cause UPDATE statements for changes to all these props to be output
            "o_data": {"name": "", "typeowner": "", "description": "", "schema": ""},
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        data = {
            "data": {"name": self.name, "schema": self.schema},
            # See issue https://github.com/Microsoft/carbon/issues/1715, 
            # Cascade should be configured
            # as part of the input to the delete method as it's not a property
            "cascade": False,
        }
        return data
