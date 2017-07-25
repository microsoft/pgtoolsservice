# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Column(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_column')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Column':
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

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str, datatype: str):
        """
        Initializes a new instance of a Column
        :param server: Connection to the server/database that this object will belong to
        :param parent: Parent object of the column, should be a Table/View
        :param name: Name of the column
        :param datatype: Type of the column
        """
        super(Column, self).__init__(server, parent, name)
        self._datatype: str = datatype

        # Declare the optional parameters
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
    def not_null(self) -> Optional[bool]:
        return self._not_null

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
