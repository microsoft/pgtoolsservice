# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from smo.common.node_object import NodeCollection, NodeObject
from smo.utils import templating


class Column(NodeObject):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent=None, **kwargs) -> 'Column':
        """
        Creates a new Database object based on the results from a query to lookup databases
        :param server: Server that owns the database
        :param parent: Parent object of the database. Should always be None
        :param kwargs: Optional parameters for the database. Values that can be provided:
        Kwargs:
            oid int: Object ID of the database
            name str: Name of the database
            spcname str: Name of the tablespace for the database
            datallowconn bool: Whether or not the database can be connected to
            cancreate bool: Whether or not the database can be created by the current user
            owner int: Object ID of the user that owns the database
            datistemplate bool: Whether or not the database is a template database
            canconnect bool: Whether or not the database is accessbile to current user
        :return: Instance of the Database
        """
        col = cls(server, parent, kwargs['name'], kwargs['type'])
        col._column_ordinal = kwargs['ordinal'] - 1
        col._is_key = kwargs['column_key'] == 'PRI'
        col._is_unique = kwargs['column_key'] == 'UNI'
        col._is_nullable = kwargs['is_nullable'] == 'YES'
        col._default_value = kwargs['column_default']
        col._is_auto_increment = 'auto_increment' in kwargs['extra']
        col._is_read_only = not kwargs['is_updatable']
        return col

    def __init__(self, server: 's.Server', parent: NodeObject, name: str, datatype: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, parent, name)
        self._datatype: str = datatype
        self._default_value: Optional[str] = None
        self._is_nullable: bool = None
        self._column_ordinal: int = None
        self._is_read_only: bool = None
        self._is_auto_increment: bool = None
        self._is_key: bool = None
        self._is_unique: bool = None
        self._default_value: str = None

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # PROPERTIES ###########################################################

    @property
    def not_null(self) -> Optional[bool]:
        return self._is_nullable

    @property
    def column_ordinal(self) -> int:
        return self._column_ordinal

    @property
    def datatype(self) -> str:
        return self._datatype

    @property
    def is_readonly(self) -> bool:
        return self._is_read_only

    @property
    def is_unique(self) -> bool:
        return self._is_unique

    @property
    def is_auto_increment(self) -> bool:
        return self._is_auto_increment

    @property
    def is_key(self) -> bool:
        return self._is_key

    @property
    def default_value(self) -> Optional[str]:
        return self._default_value
