# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import List, Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
import pgsmo.utils as utils


TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Schema:
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper) -> List['Schema']:
        type_template_root = path.join(TEMPLATE_ROOT, conn.server_type)
        return node.get_nodes(conn, type_template_root, cls._from_node_query)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Schema':
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
        schema = cls(kwargs['name'])
        schema._conn = conn
        schema._oid = kwargs['oid']
        schema._can_create = kwargs['can_create']
        schema._has_usage = kwargs['has_usage']

        return schema

    def __init__(self, name: str):
        #

        self._name: str = name

        # Declare the optional parameters
        self._conn: utils.querying.ConnectionWrapper = None
        self._oid: Optional[int] = None
        self._can_create: Optional[bool] = None
        self._has_usage: Optional[bool] = None

        # Declare the child items
        self._tables: List[Table] = []
        self._views: List[View] = []

    # PROPERTIES ###########################################################
    @property
    def can_create(self) -> Optional[bool]:
        return self._can_create

    @property
    def has_usage(self) -> Optional[bool]:
        return self._has_usage

    @property
    def name(self) -> str:
        return self._name

    @property
    def oid(self) -> Optional[int]:
        return self._oid

    @property
    def tables(self) -> List[Table]:
        return self._tables

    @property
    def views(self) -> List[View]:
        return self._views

    # METHODS ##############################################################
    def refresh(self) -> None:
        self._tables = Table.get_tables_for_schema(self._conn, self._oid)
        self._views = View.get_views_for_schema(self._conn, self._oid)
