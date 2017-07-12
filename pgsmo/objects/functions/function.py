# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_functions')


class Function(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection, schema_id: int) -> List['Function']:
        type_template_root = os.path.join(TEMPLATE_ROOT, conn.server_type)
        return node.get_nodes(conn, type_template_root, cls._from_node_query, scid=schema_id)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Function':
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
        super(Function, self).__init__(conn, name)

        # Declare the basic properties
        self._description: Optional[str] = None
        self._lanname: Optional[str] = None
        self._owner: Optional[str] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def description(self) -> Optional[str]:
        """Description of the function"""
        return self._description

    @property
    def language(self) -> Optional[str]:
        """The name of the language the function was written in"""
        return self._lanname

    @property
    def owner(self) -> Optional[str]:
        """The name of the owner of the function"""
        return self._owner
