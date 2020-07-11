# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta
from typing import List, Optional

from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import PGserver    # noqa
import smo.utils.templating as templating


class FunctionBase(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate, metaclass=ABCMeta):
    """Base class for Functions. Provides basic properties for all Function types"""

    MACRO_ROOT = templating.get_template_root(__file__, 'macros')
    GLOBAL_MACRO_ROOT = templating.get_template_root(__file__, '../global_macros')

    @classmethod
    def _from_node_query(cls, server: PGserver, parent: NodeObject, **kwargs) -> 'FunctionBase':
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
        func._schema = kwargs['schema']
        func._scid = kwargs['schemaoid']
        func._is_system = kwargs['is_system']

        return func

    def __init__(self, server: PGserver, parent: NodeObject, name: str):
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare the basic properties
        self._description: Optional[str] = None
        self._language_name: Optional[str] = None
        self._owner: Optional[str] = None
        self._schema: str = None
        self._scid: int = None

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.scid,
            'fnid': self.oid
        }
        return template_vars

    # -BASIC PROPERTIES ####################################################
    @property
    def schema(self):
        return self._schema

    @property
    def scid(self):
        return self._scid

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def language_name(self) -> Optional[str]:
        return self._language_name

    @property
    def owner(self) -> Optional[str]:
        return self._owner

    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def xmin(self):
        return self._full_properties.get("xmin", "")

    @property
    def proname(self):
        return self._full_properties.get("proname", "")

    @property
    def pronamespace(self):
        return self._full_properties.get("pronamespace", "")

    @property
    def proowner(self):
        return self._full_properties.get("proowner", "")

    @property
    def prolang(self):
        return self._full_properties.get("prolang", "")

    @property
    def provariadic(self):
        return self._full_properties.get("provariadic", "")

    @property
    def protransform(self):
        return self._full_properties.get("protransform", "")

    @property
    def proisagg(self):
        return self._full_properties.get("proisagg", "")

    @property
    def pronargs(self):
        return self._full_properties.get("pronargs", "")

    @property
    def pronargdefaults(self):
        return self._full_properties.get("pronargdefaults", "")

    @property
    def prorettype(self):
        return self._full_properties.get("prorettype", "")

    @property
    def proargtypes(self):
        return self._full_properties.get("proargtypes", "")

    @property
    def proallargtypes(self):
        return self._full_properties.get("proallargtypes", "")

    @property
    def proargmodes(self):
        return self._full_properties.get("proargmodes", "")

    @property
    def proargdefaults(self):
        return self._full_properties.get("proargdefaults", "")

    @property
    def protrftypes(self):
        return self._full_properties.get("protrftypes", "")

    @property
    def proconfig(self):
        return self._full_properties.get("proconfig", "")

    @property
    def proacl(self):
        return self._full_properties.get("proacl", "")

    @property
    def typnsp(self):
        return self._full_properties.get("typnsp", "")

    @property
    def arguments(self) -> Optional[str]:
        return self._full_properties.get("arguments", "")

    @property
    def proargdefaultvals(self) -> Optional[str]:
        return self._full_properties.get("proargdefaultvals", "")

    @property
    def proargnames(self) -> Optional[str]:
        return self._full_properties.get("proargnames", "")

    @property
    def proargtypenames(self) -> Optional[str]:
        return self._full_properties.get("proargtypenames", "")

    @property
    def proretset(self):
        return self._full_properties.get("proretset", "")

    @property
    def prorettypename(self):
        return self._full_properties.get("prorettypename", "")

    @property
    def procost(self):
        return self._full_properties.get("procost", "")

    @property
    def provolatile(self):
        return self._full_properties.get("provolatile", "")

    @property
    def proleakproof(self):
        return self._full_properties.get("proleakproof", "")

    @property
    def proisstrict(self):
        return self._full_properties.get("proisstrict", "")

    @property
    def prosecdef(self):
        return self._full_properties.get("prosecdef", "")

    @property
    def proiswindow(self):
        return self._full_properties.get("proiswindow", "")

    @property
    def proparallel(self):
        return self._full_properties.get("proparallel", "")

    @property
    def prorows(self):
        return self._full_properties.get("prorows", "")

    @property
    def variables(self):
        return self._full_properties.get("variables", "")

    @property
    def probin(self):
        return self._full_properties.get("probin", "")

    @property
    def prosrc_c(self):
        return self._full_properties.get("prosrc_c", "")

    @property
    def prosrc(self):
        return self._full_properties.get("prosrc", "")

    @property
    def func_args_without(self):
        return self._full_properties.get("func_args_without", "")

    @property
    def acl(self):
        return self._full_properties.get("acl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def change_func(self):
        return self._full_properties.get("change_func", "")

    @property
    def merged_variables(self):
        return self._full_properties.get("merged_variables", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> List[str]:
        return [cls.MACRO_ROOT, cls.GLOBAL_MACRO_ROOT]

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {"data": {
            "name": self.name,
            "pronamespace": self.schema,
            "arguments": self.arguments,
            "proretset": self.proretset,
            "prorettypename": self.prorettypename,
            "lanname": self.language_name,
            "procost": self.procost,
            "provolatile": self.provolatile,
            "proleakproof": self.proleakproof,
            "proisstrict": self.proisstrict,
            "prosecdef": self.prosecdef,
            "proiswindow": self.proiswindow,
            "proparallel": self.proparallel,
            "prorows": self.prorows,
            "variables": self.variables,
            "probin": self.probin,
            "prosrc_c": self.prosrc_c,
            "prosrc": self.prosrc,
            "funcowner": self.owner,
            "func_args_without": self.func_args_without,
            "description": self.description,
            "acl": self.acl,
            "seclabels": self.seclabels
        }}

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "name": self.name,
            "nspname": self.schema,
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "pronamespace": self.schema,
                "arguments": self.arguments,
                "lanname": self.language_name,
                "procost": self.procost,
                "provolatile": self.provolatile,
                "proisstrict": self.proisstrict,
                "prosecdef": self.prosecdef,
                "proiswindow": self.proiswindow,
                "prorows": self.prorows,
                "variables": self.variables,
                "probin": self.probin,
                "prosrc": self.prosrc,
                "funcowner": self.owner,
                "description": self.description,
                "acl": self.acl,
                "seclabels": self.seclabels,
                "change_func": self.change_func,
                "merged_variables": self.merged_variables
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
