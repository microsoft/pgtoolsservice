# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Optional

import pgsmo.objects.node_object as node
import pgsmo.utils as utils

TEMPLATE_ROOT = utils.templating.get_template_root(__file__, 'templates')


class Column:
    @classmethod
    def get_nodes_for_parent(cls, conn: utils.querying.ConnectionWrapper, tid: int) -> List['Column']:
        return node.get_nodes(conn, TEMPLATE_ROOT, cls._from_node_query, tid=tid)

    @classmethod
    def _from_node_query(cls, conn: utils.querying.ConnectionWrapper, **kwargs) -> 'Column':
        """
        Creates a new Column object based on the the results from the column nodes query
        :param conn: Connection used to execute the column nodes query
        :param kwargs: Optional parameters for the column
        Kwargs:
            name str: Name of the column
            datatype str: Name of the type of the column
            oid int: Object ID of the column
            not_null bool: Whether or not null is allowed for the column
            has_default_value bool: Whether or not the column has a default value constraint
        :return: Instance of the Column
        """
        col = cls(kwargs['name'], kwargs['datatype'])
        col._conn = conn
        col._cid = kwargs['oid']
        col._has_default_value = kwargs['has_default_value']
        col._not_null = kwargs['not_null']

        return col

    def __init__(self, name: str, datatype: str):
        """
        Initializes a new instance of a Column
        :param name: Name of the column
        :param datatype: Type of the column
        """
        self._name: str = name
        self._datatype: str = datatype

        # Declare the optional parameters
        self._conn: Optional[utils.querying.ConnectionWrapper] = None
        self._cid: Optional[int] = None
        self._has_default_value: Optional[bool] = None
        self._not_null: Optional[bool] = None

    # PROPERTIES ###########################################################
    @property
    def datatype(self) -> str:
        return self._datatype

    @property
    def has_default_value(self) -> Optional[bool]:
        return self._has_default_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def not_null(self) -> Optional[bool]:
        return self._not_null

    @property
    def oid(self) -> Optional[int]:
        return self._cid

    # METHODS ##############################################################
    def refresh(self):
        self._fetch_properties()

    # IMPLEMENTATION DETAILS ###############################################
    def _fetch_properties(self):
        pass
