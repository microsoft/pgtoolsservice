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

        col._column_ordinal = kwargs['oid'] - 1
        col._is_key = kwargs['isprimarykey']
        col._is_readonly = kwargs['is_updatable'] is False
        col._is_unique = kwargs['isunique']
        col._type_oid = kwargs['typoid']
        col._default_value = kwargs['default'] if col._has_default_value is True else None
        col._is_auto_increament = col._default_value is not None and col._default_value.startswith('nextval(')

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

        self._has_default_value: Optional[bool] = None
        self._not_null: Optional[bool] = None

        self._column_ordinal: int = None
        self._is_key: bool = None
        self._is_readonly: bool = None
        self._is_unique: bool = None
        self._type_oid: int = None
        self._default_value: Optional[str] = None
        self._is_auto_increament = None

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

    @property
    def column_ordinal(self) -> int:
        return self._column_ordinal

    @property
    def is_key(self) -> bool:
        return self._is_key

    @property
    def is_readonly(self) -> bool:
        return self._is_readonly

    @property
    def is_unique(self) -> bool:
        return self._is_unique

    @property
    def type_oid(self) -> int:
        return self._type_oid

    @property
    def default_value(self) -> Optional[str]:
        return self._default_value

    @property
    def is_auto_increament(self) -> bool:
        return self._is_auto_increament

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT
