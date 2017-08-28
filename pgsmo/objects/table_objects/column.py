# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional, List

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Column(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_column')
    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Column':
        """
        Creates a new Column object based on the the results from the column nodes query
        :param server: Server that owns the column
        :param parent: Parent object of the column. Should be a Table/View
        :param kwargs: Optional parameters for the column
        Kwargs:
            name str: Name of the column
            datatype str: Name of the type of the column
            oid int: Object ID of the column
            not_null bool: Whether or not null is allowed for the column
            has_default_value bool: Whether or not the column has a default value constraint
        :return: Instance of the Column
        """
        col = cls(server, parent, kwargs['name'], kwargs['datatype'])
        col._oid = kwargs['oid']
        col._has_default_value = kwargs['has_default_val']
        col._not_null = kwargs['not_null']

        return col

    def __init__(self, server: 's.Server', parent: NodeObject, name: str, datatype: str):
        """
        Initializes a new instance of a Column
        :param server: Connection to the server/database that this object will belong to
        :param parent: Parent object of the column, should be a Table/View
        :param name: Name of the column
        :param datatype: Type of the column
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        self._datatype: str = datatype

        # Declare the optional parameters
        self._has_default_value: Optional[bool] = None
        self._not_null: Optional[bool] = None

    # PROPERTIES ###########################################################
    @property
    def name(self):
        return self._full_properties.get("name", "")

    @property
    def cltype(self):
        return self._full_properties.get("cltype", "")

    @property
    def schema(self):
        return self._full_properties.get("schema", "")

    @property
    def table(self):
        return self._full_properties.get("table", "")

    @property
    def displaytypname(self):
        return self._full_properties.get("displaytypname", "")

    @property
    def attlen(self):
        return self._full_properties.get("attlen", "")

    @property
    def attprecision(self):
        return self._full_properties.get("attprecision", "")

    @property
    def hasSqrBracket(self):
        return self._full_properties.get("hasSqrBracket", "")

    @property
    def collspcname(self):
        return self._full_properties.get("collspcname", "")

    @property
    def attnotnull(self):
        return self._full_properties.get("attnotnull", "")

    @property
    def defval(self):
        return self._full_properties.get("defval", "")
    
    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def attoptions(self):
        return self._full_properties.get("attoptions", "")

    @property
    def attacl(self):
        return self._full_properties.get("attacl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")
    
    @property
    def attstattarget(self):
        return self._full_properties.get("attstattarget", "")
    
    @property
    def attstorage(self):
        return self._full_properties.get("attstorage", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
         return [cls.MACRO_ROOT]
    
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "name": self.name,
                "cltype": self.cltype,
                "schema": self.schema,
                "table": self.table,
                "displaytypname": self.displaytypname,
                "attlen": self.attlen,
                "attprecision": self.attprecision,
                "hasSqrBracket": self.hasSqrBracket,
                "collspcname": self.collspcname,
                "attnotnull": self.attnotnull,
                "defval": self.defval,
                "description": self.description,
                "attoptions": self.attoptions,
                "attacl": self.attacl,
                "seclabels": self.seclabels                                
            }
        }        

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "schema": self.schema,
                "table": self.table,
                "name": self.name
            }             
        }        

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "table": self.table,
                "cltype": self.cltype,
                "attlen": self.attlen,
                "attprecision": self.attprecision,
                "collspcname": self.collspcname,
                "defval": self.defval,
                "attnotnull": self.attnotnull,
                "attstattarget": self.attstattarget,
                "attstorage": self.attstorage,
                "description": self.description,
                "attoptions": self.attoptions,
                "attacl": self.attacl,
                "seclabels": self.seclabels
            },
            "o_data": {
                "name": "",
                "cltype": "",
                "attlen": "",
                "attprecision": "",
                "collspcname": "",
                "defval": "",
                "attnotnull": "",
                "attstattarget": "",
                "attstorage": ""
            }
        }