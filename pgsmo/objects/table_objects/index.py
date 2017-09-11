# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from pgsmo.objects.node_object import NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class Index(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates_index')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Index':
        """
        Creates a new Index object based on the results of a nodes query
        :param server: Server that owns the index
        :param parent: Parent object of the Index. Should be Table/View
        :param kwargs: Parameters for the index
        Kwargs:
            name str: The name of the index
            oid int: Object ID of the index
        :return: Instance of the Index
        """
        idx = cls(server, parent, kwargs['name'])
        idx._oid = kwargs['oid']

        return idx

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
        """
        Initializes a new instance of an Index
        :param server: Server that owns the index
        :param parent: Parent object of the index. Should be Table/View
        :param name: Name of the index
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Full Object Properties
        self._is_clustered: Optional[bool] = None
        self._is_primary: Optional[bool] = None
        self._is_unique: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -FULL OBJECT PROPERTIES ##############################################
    @property
    def is_clustered(self) -> Optional[bool]:
        return self._full_properties['is_clustered']

    @property
    def is_valid(self) -> Optional[bool]:
        return self._full_properties['is_valid']

    @property
    def is_unique(self) -> Optional[bool]:
        return self._full_properties['is_unique']

    @property
    def is_primary(self) -> Optional[bool]:
        return self._full_properties['is_primary']

    @property
    def is_concurrent(self):
        return self._full_properties["is_concurrent"]

    @property
    def amname(self):
        return self._full_properties["amname"]

    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def fillfactor(self):
        return self._full_properties["fillfactor"]

    @property
    def spcname(self):
        return self._full_properties["spcname"]

    @property
    def indconstraint(self):
        return self._full_properties["indconstraint"]

    @property
    def mode(self):
        return self._full_properties["mode"]

    @property
    def index(self):
        return self._full_properties["index"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    @property
    def description(self):
        return self._full_properties["description"]

    @property
    def extended_vars(self):
        return {
            'tid': self.parent.oid,                 # Table/view OID
            'did': self.parent.parent.parent.oid    # Database OID
        }
    # IMPLEMENTATION DETAILS ###############################################

    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "indisunique": self.is_unique,
                "isconcurrent": self.is_concurrent,
                "name": self.name,
                "schema": self.parent.parent.name,
                "table": self.parent.name,
                "amname": self.amname,
                "columns": self.columns,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "indconstraint": self.indconstraint
            },
            "mode": self.mode
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "nspname": self.parent.parent.name,
                "name": self.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "schema": self.parent.parent.name,
                "fillfactor": self.fillfactor,
                "spcname": self.spcname,
                "indisclustered": self.is_clustered,
                "table": self.parent.name,
                "description": self.description
            },
            "o_data": {
                "name": "",
                "fillfactor": "",
                "spcname": "",
                "indisclustered": "",
                "description": ""
            }
        }
