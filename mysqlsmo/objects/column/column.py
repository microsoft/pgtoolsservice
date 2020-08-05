# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from smo.common.node_object import NodeCollection, NodeObject
from smo.utils import templating


class Column(NodeObject):

    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: None, **kwargs) -> 'Column':
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
        col = cls(server, kwargs['name'], kwargs['type'])

        return col

    def __init__(self, server: 's.Server', name: str, datatype: str):
        """
        Initializes a new instance of a database
        """
        NodeObject.__init__(self, server, None, name)
        self._datatype: str = datatype
        self._default_value: Optional[str] = None

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # PROPERTIES ###########################################################

    @property
    def not_null(self) -> Optional[bool]:
        pass

    @property
    def column_ordinal(self) -> int:
        pass

    @property
    def datatype(self) -> str:
        pass

    @property
    def is_readonly(self) -> bool:
        pass

    @property
    def is_unique(self) -> bool:
        pass

    @property
    def is_auto_increment(self) -> bool:
        pass

    @property
    def is_key(self) -> bool:
        pass

    @property
    def default_value(self) -> Optional[str]:
        return self._default_value
