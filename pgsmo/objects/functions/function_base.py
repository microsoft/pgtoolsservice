# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta
from typing import Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating
from pgsmo.objects.server import server as s    # noqa



class FunctionBase(node.NodeObject, metaclass=ABCMeta):
    """Base class for Functions. Provides basic properties for all Function types"""

    MACRO_ROOT = templating.get_template_root(__file__, 'macros')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'FunctionBase':
        """
        Creates a Function instance from the results of a node query
        :param server: Server that owns the function
        :param parent: Parent object of the function
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the function
            name str: Signature of the function
            lanname str: Name of the language the function is written in
            funcowner str: Name of the owner of the function
            description str: Description of the function
        :return: A Function instance
        """
        func = cls(server, parent, kwargs['name'])
        func._oid = kwargs['oid']
        func._language_name = kwargs['lanname']
        func._owner = kwargs['funcowner']
        func._description = kwargs['description']

        return func

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(FunctionBase, self).__init__(server, parent, name)

        # Declare the basic properties
        self._description: Optional[str] = None
        self._language_name: Optional[str] = None
        self._owner: Optional[str] = None

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.parent.oid,
            'did': self.parent.parent.oid,
            'datlastsysoid': 0  # temporary until implemented
        }
        return template_vars
    
    # -BASIC PROPERTIES ####################################################
    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def language_name(self) -> Optional[str]:
        return self._language_name

    @property
    def owner(self) -> Optional[str]:
        return self._owner   

    def getExtendedProperties(self, propertyName: str, default = None):
        """ Function to get properties """
        return self._full_properties.get(propertyName, default)

    def create_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve create scripts for a functions """

        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(connection, query_file, data, paths_to_add=[self.MACRO_ROOT])


    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        data = {"data": {
            "name": self.getExtendedProperties("name"),
            "pronamespace": self.parent.name,
            "arguments": self.getExtendedProperties("arguments", []),
            "proretset": self.getExtendedProperties("proretset"),
            "prorettypename" : self.getExtendedProperties("prorettypename"),
            "lanname": self.language_name,
            "procost": self.getExtendedProperties("procost"),
            "provolatile": self.getExtendedProperties("provolatile"),
            "proleakproof": self.getExtendedProperties("proleakproof"),
            "proisstrict": self.getExtendedProperties("proisstrict"),
            "prosecdef": self.getExtendedProperties("prosecdef"),
            "proiswindow": self.getExtendedProperties("proiswindow"),
            "proparallel": self.getExtendedProperties("proiswindow"),
            "prorows": self.getExtendedProperties("proiswindow"),
            "variables": self.getExtendedProperties("variables"),
            "probin": self.getExtendedProperties("probin"),
            "prosrc_c": self.getExtendedProperties("prosrc_c"),
            "prosrc": self.getExtendedProperties("prosrc"),
            "funcowner": self.owner,
            "func_args_without": self.getExtendedProperties("func_args_without", ""),
            "description": self.description,
            "acl": self.getExtendedProperties("acl"),
            "seclabels": self.getExtendedProperties("seclabels")
        }}
        return data