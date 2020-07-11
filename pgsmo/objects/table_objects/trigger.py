# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Optional

from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import PGserver    # noqa
import smo.utils.templating as templating


class Trigger(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'trigger')

    @classmethod
    def _from_node_query(cls, server: PGserver, parent: NodeObject, **kwargs) -> 'Trigger':
        """
        Creates a new Trigger object based on the results of a nodes query
        :param server: Server that owns the trigger
        :param parent: Parent object of the Trigger. Should be Table/View
        :param kwargs: Parameters for the trigger
        Kwargs:
            oid int: Object ID of the trigger
            name str: Name of the trigger
            is_enable_trigger bool: Whether or not the trigger is enabled
        :return: Instance of a Trigger
        """
        trigger = cls(server, parent, kwargs['name'])
        trigger._oid = kwargs['oid']

        # Basic properties
        trigger._is_enabled = kwargs['is_enable_trigger']

        return trigger

    def __init__(self, server: PGserver, parent: NodeObject, name: str):
        """
        Initializes a new instance of a trigger
        :param server: Connection the trigger belongs to
        :param parent: Parent object of the trigger. Should be Table/View
        :param name: Name of the trigger
        """
        NodeObject.__init__(self, server, parent, name)
        ScriptableCreate.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableDelete.__init__(self, self._template_root(server), self._macro_root(), server.version)
        ScriptableUpdate.__init__(self, self._template_root(server), self._macro_root(), server.version)

        # Declare Trigger-specific basic properties
        self._is_enabled: Optional[bool] = None

    # PROPERTIES ###########################################################
    # -BASIC PROPERTIES ####################################################
    @property
    def is_enabled(self) -> Optional[bool]:
        """Whether or not the trigger is enabled"""
        return self._is_enabled

    # -FULL OBJECT PROPERTIES ##############################################

    @property
    def lanname(self):
        return self._full_properties["lanname"]

    @property
    def tfunction(self):
        return self._full_properties["tfunction"]

    @property
    def is_constraint_trigger(self):
        return self._full_properties["is_constraint_trigger"]

    @property
    def fires(self):
        return self._full_properties["fires"]

    @property
    def evnt_insert(self):
        return self._full_properties["evnt_insert"]

    @property
    def evnt_delete(self):
        return self._full_properties["evnt_delete"]

    @property
    def evnt_truncate(self):
        return self._full_properties["evnt_truncate"]

    @property
    def evnt_update(self):
        return self._full_properties["evnt_update"]

    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def deferrable(self):
        return self._full_properties["deferrable"]

    @property
    def initdeferred(self):
        return self._full_properties["initdeferred"]

    @property
    def is_row_trigger(self):
        return self._full_properties["is_row_trigger"]

    @property
    def whenclause(self):
        return self._full_properties["whenclause"]

    @property
    def prosrc(self):
        return self._full_properties["prosrc"]

    @property
    def args(self):
        return self._full_properties["args"]

    @property
    def description(self):
        return self._full_properties["description"]

    @property
    def cascade(self):
        return self._full_properties["cascade"]

    @property
    def is_enable_trigger(self):
        return self._full_properties["is_enable_trigger"]

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: PGserver) -> str:
        return cls.TEMPLATE_ROOT

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        return {
            "data": {
                "lanname": self.lanname,
                "tfunction": self.tfunction,
                "name": self.name,
                "is_constraint_trigger": self.is_constraint_trigger,
                "fires": self.fires,
                "evnt_insert": self.evnt_insert,
                "evnt_delete": self.evnt_delete,
                "evnt_truncate": self.evnt_truncate,
                "evnt_update": self.evnt_update,
                "columns": self.columns,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "tgdeferrable": self.deferrable,
                "tginitdeferred": self.initdeferred,
                "is_row_trigger": self.is_row_trigger,
                "whenclause": self.whenclause,
                "prosrc": self.prosrc,
                "tgargs": self.args,
                "description": self.description,
            }
        }

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "nspname": self.parent.schema,
                "relname": self.parent.name
            },
            "cascade": self.cascade
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        return {
            "data": {
                "name": self.name,
                "prosrc": self.prosrc,
                "is_row_trigger": self.is_row_trigger,
                "evnt_insert": self.evnt_insert,
                "evnt_delete": self.evnt_delete,
                "evnt_update": self.evnt_update,
                "fires": self.fires,
                "evnt_truncate": self.evnt_truncate,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "description": self.description,
                "is_enable_trigger": self.is_enable_trigger
            },
            "o_data": {
                "name": "",
                "nspname": "",
                "relname": "",
                "lanname": "",
                "prosrc": "",
                "is_row_trigger": "",
                "evnt_insert": "",
                "evnt_delete": "",
                "evnt_update": "",
                "fires": "",
                "evnt_truncate": "",
                "columns": "",
                "tgdeferrable": "",
                "tginitdeferred": "",
                "whenclause": "",
                "description": "",
                "is_enable_trigger": ""
            }
        }
