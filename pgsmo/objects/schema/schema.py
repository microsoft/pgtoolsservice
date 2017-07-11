# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.functions.function import Function
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')


class Schema(node.NodeObject):
    @classmethod
    def get_nodes_for_parent(cls, conn: querying.ServerConnection) -> List['Schema']:
        type_template_root = path.join(TEMPLATE_ROOT, conn.server_type)
        return node.get_nodes(conn, type_template_root, cls._from_node_query)

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'Schema':
        """
        Creates an instance of a schema object from the results of a nodes query
        :param conn: The connection used to execute the nodes query
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the schema
            oid int: Object ID of the schema
            can_create bool: Whether or not the schema can be created by the current user
            has_usage bool: Whether or not the schema can be used(?)
        :return:
        """
        schema = cls(conn, kwargs['name'])
        schema._oid = kwargs['oid']
        schema._can_create = kwargs['can_create']
        schema._has_usage = kwargs['has_usage']

        return schema

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(Schema, self).__init__(conn, name)

        # Declare the optional parameters
        self._can_create: Optional[bool] = None
        self._has_usage: Optional[bool] = None

        # Declare the child items
        self._functions: node.NodeCollection = self._register_child_collection(
            lambda: Function.get_nodes_for_parent(self._conn, self._oid)
        )
        self._tables: node.NodeCollection = self._register_child_collection(
            lambda: Table.get_nodes_for_parent(self._conn, self._oid)
        )
        self._views: node.NodeCollection = self._register_child_collection(
            lambda: View.get_nodes_for_parent(self._conn, self._oid)
        )

    # PROPERTIES ###########################################################
    @property
    def can_create(self) -> Optional[bool]:
        return self._can_create

    @property
    def has_usage(self) -> Optional[bool]:
        return self._has_usage

    # -CHILD OBJECTS #######################################################
    @property
    def functions(self) -> node.NodeCollection:
        return self._functions

    @property
    def tables(self) -> node.NodeCollection:
        return self._tables

    @property
    def views(self) -> node.NodeCollection:
        return self._views
