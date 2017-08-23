# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional, List, Any

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.server import server as s        # noqa
import pgsmo.utils.templating as templating

TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
MACRO_ROOT = templating.get_template_root(__file__, 'macros')


class DataType(NodeObject):
    """Represents a data type"""

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'DataType':
        """
        Creates a Type object from the result of a DataType node query
        :param server: Server that owns the DataType
        :param parent: Parent object of the DataType
        :param kwargs: Row from a DataType node query
        Kwargs:
            name str: Name of the DataType
            oid int: Object ID of the DataType
            rolcanlogin bool: Whether or not the DataType can login
            rolsuper bool: Whether or not the DataType is a super user
        :return: A DataType7 instance
        """
        datatype = cls(server, parent, kwargs['name'])

        # Define values from node query
        datatype._oid = kwargs['oid']
        return datatype

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes internal state of a DataType object
        :param server: Server that owns the role
        :param name: Name of the role
        """
        super(DataType, self).__init__(server, parent, name)
        self._additional_properties: NodeLazyPropertyCollection = self._register_property_collection(self._additional_property_generator)

    # PROPERTIES ###########################################################
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
    def schema(self):
        return self.parent.name

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
    def composite(self) -> List[Any]:
        if not self.typtype == 'c':
            return None
        composite = []
        # TODO support composite, which is a complex property
        return composite

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return TEMPLATE_ROOT

    @classmethod
    def _macro_root(cls) -> List[str]:
        return [MACRO_ROOT]

    # SCRIPTING METHODS ####################################################

    def create_script(self) -> str:
        """ Function to retrieve create scripts for a DataType """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(query_file, data, paths_to_add=self._macro_root())

    def update_script(self) -> str:
        """ Function to retrieve update scripts for a DataType """
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(query_file, data, paths_to_add=self._macro_root())

    def delete_script(self) -> str:
        """ Function to retrieve delete scripts for datatype """
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(query_file, data)

    # HELPER METHODS ##################################################################

    def _create_query_data(self):
        """ Gives the data object for create query """
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
                "composite": self.composite
            }
        }

    def _update_query_data(self):
        """ Gives the data object for update query """
        return {
            "data": {
                "name": self.name,
                "typeowner": self.typeowner,
                "description": self.description,
                "schema": self.schema,
            },
            # This will cause UPDATE statements for changes to all these props to be output
            "o_data": {
                "name": "",
                "typeowner": "",
                "description": "",
                "schema": ""
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        data = {
            "data": {
                "name": self.name,
                "schema": self.parent.name
            },
            # See issue https://github.com/Microsoft/carbon/issues/1715, Cascade should be configured
            # as part of the input to the delete method as it's not a property
            "cascade": False
        }
        return data
