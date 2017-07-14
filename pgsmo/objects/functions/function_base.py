# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying


class FunctionBase(node.NodeObject, metaclass=ABCMeta):
    """Base class for Functions. Provides basic properties for all Function types"""

    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, scid: int) -> List['FunctionBase']:
        """
        Generates a list of functions by executing nodes.sql
        :param conn: The connection to use to execute the nodes query
        :param scid: Object ID of the schema that owns the constraints
        :return: A list of FunctionBase objects (can be any of the FunctionBase subclasses)
        """
        return node.get_nodes(conn, cls._template_path(conn), cls._from_node_query, scid=scid)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'FunctionBase':
        """
        Creates a Function instance from the results of a node query
        :param conn: The connection used to execute the node query
        :param kwargs: A row from the node query
        Kwargs:
            oid int: Object ID of the function
            name str: Signature of the function
            lanname str: Name of the language the function is written in
            funcowner str: Name of the owner of the function
            description str: Description of the function
        :return: A Function instance
        """
        func = cls(conn, kwargs['name'])
        func._oid = kwargs['oid']
        func._lanname = kwargs['lanname']
        func._owner = kwargs['funcowner']
        func._description = kwargs['description']

        return func

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(FunctionBase, self).__init__(conn, name)

        # Declare the basic properties
        self._description: Optional[str] = None
        self._lanname: Optional[str] = None
        self._owner: Optional[str] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def language_name(self) -> Optional[str]:
        return self._lanname

    @property
    def owner(self) -> Optional[str]:
        return self._owner

    # METHODS ##############################################################
    @classmethod
    @abstractmethod
    def _template_path(cls, conn: querying.ServerConnection) -> str:
        pass
