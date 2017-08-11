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

    # SCRIPTING METHODS ##############################################################
    def create_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve create scripts for a functions """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(connection, query_file, data, paths_to_add=[self.MACRO_ROOT])

    def delete_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve delete scripts for a functions"""
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(connection, query_file, data)

    def update_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve update scripts for a functions"""
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(connection, query_file, data, paths_to_add=[self.MACRO_ROOT])

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        data = {"data": {
            "name": self._full_properties.get("name"),
            "pronamespace": self.parent.name,
            "arguments": self._full_properties.get("arguments", []),
            "proretset": self._full_properties.get("proretset"),
            "prorettypename": self._full_properties.get("prorettypename"),
            "lanname": self.language_name,
            "procost": self._full_properties.get("procost"),
            "provolatile": self._full_properties.get("provolatile"),
            "proleakproof": self._full_properties.get("proleakproof"),
            "proisstrict": self._full_properties.get("proisstrict"),
            "prosecdef": self._full_properties.get("prosecdef"),
            "proiswindow": self._full_properties.get("proiswindow"),
            "proparallel": self._full_properties.get("proiswindow"),
            "prorows": self._full_properties.get("proiswindow"),
            "variables": self._full_properties.get("variables"),
            "probin": self._full_properties.get("probin"),
            "prosrc_c": self._full_properties.get("prosrc_c"),
            "prosrc": self._full_properties.get("prosrc"),
            "funcowner": self.owner,
            "func_args_without": self._full_properties.get("func_args_without", ""),
            "description": self.description,
            "acl": self._full_properties.get("acl"),
            "seclabels": self._full_properties.get("seclabels")
        }}
        return data

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        data = {
            "scid": self.extended_vars['scid'],
            "fnid": self.extended_vars['fnid'],
            "cascade": self._full_properties.get("cascade", ""),
        }
        return data

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        data = {
            "data": {
                "name": self._full_properties.get("name"),
                "pronamespace": self.parent.name,
                "arguments": self._full_properties.get("arguments", []),
                "lanname": self.language_name,
                "procost": self._full_properties.get("procost"),
                "provolatile": self._full_properties.get("provolatile"),
                "proisstrict": self._full_properties.get("proisstrict"),
                "prosecdef": self._full_properties.get("prosecdef"),
                "proiswindow": self._full_properties.get("proiswindow"),
                "prorows": self._full_properties.get("proiswindow"),
                "variables": self._full_properties.get("variables"),
                "probin": self._full_properties.get("probin"),
                "prosrc": self._full_properties.get("prosrc"),
                "funcowner": self.owner,
                "description": self.description,
                "acl": self._full_properties.get("acl"),
                "seclabels": self._full_properties.get("seclabels"),
                "change_func": self._full_properties.get("change_func"),
                "merged_variables": self._full_properties.get("merged_variables")
            },
            "o_data": {
                "name": "",
                "pronamespace": "",
                "proargtypenames": "",
                "lanname": "",
                "provolatile": "",
                "proisstrict": "",
                "prosecdef": "",
                "proiswindow": "",
                "procost": "",
                "prorows": "",
                "probin": "",
                "prosrc_c": "",
                "prosrc": ""
            }
        }
        return data
