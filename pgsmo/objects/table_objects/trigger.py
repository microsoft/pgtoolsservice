# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from typing import Optional

from smo.common.node_object import NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server import server as s    # noqa
import smo.utils.templating as templating


class Trigger(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'trigger')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: NodeObject, **kwargs) -> 'Trigger':
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

    def __init__(self, server: 's.Server', parent: NodeObject, name: str):
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
    def tgtype(self):
        return self._full_properties["tgtype"]

    @property
    def tfunction(self):
        return self._full_properties["tfunction"]

    @property
    def is_constraint_trigger(self):
        return self._full_properties["is_constraint_trigger"]

    @property
    def columns(self):
        return self._full_properties["columns"]

    @property
    def tgdeferrable(self):
        return self._full_properties["tgdeferrable"]

    @property
    def tginitdeferred(self):
        return self._full_properties["tginitdeferred"]

    @property
    def whenclause(self):
        return self._full_properties["whenclause"]

    @property
    def prosrc(self):
        return self._full_properties["prosrc"]

    @property
    def description(self):
        return self._full_properties["description"]

    @property
    def is_enable_trigger(self):
        return self._full_properties["is_enable_trigger"]

    @property
    def custom_tgargs(self):
        return self._full_properties["custom_tgargs"]

    @property
    def tgattr(self):
        return self._full_properties["tgattr"]

    @property
    def tgfoid(self):
        return self._full_properties["tgfoid"]

    @property
    def extended_vars(self):
        return {
            'tid': self.parent.oid,
            'trid': self.oid,
            'datlastsysoid': self.get_database_node().datlastsysoid
        }

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return os.path.join(cls.TEMPLATE_ROOT, server.server_type)

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        query_data = {
            "data": {
                "tgtype": self.tgtype,
                "lanname": self.lanname,
                "custom_tgargs": self.custom_tgargs,
                "tgattr": self.tgattr,
                "name": self.name,
                "is_constraint_trigger": self.is_constraint_trigger,
                "schema": self.parent.schema,
                "table": self.parent.name,
                "tgdeferrable": self.tgdeferrable,
                "tginitdeferred": self.tginitdeferred,
                "whenclause": self.whenclause,
                "prosrc": self.prosrc,
                "description": self.description,
            }
        }

        self._trigger_definition(query_data['data'])
        self._get_trigger_function_and_columns(query_data['data'])
        return query_data

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        return {
            "data": {
                "name": self.name,
                "nspname": self.parent.schema,
                "relname": self.parent.name
            },
            "cascade": True
        }

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        query_data = {
            "tgtype": self.tgtype,
            "lanname": self.lanname,
            "custom_tgargs": self.custom_tgargs,
            "tgattr": self.tgattr,
            "name": self.name,
            "is_constraint_trigger": self.is_constraint_trigger,
            "schema": self.parent.schema,
            "table": self.parent.name,
            "tgdeferrable": self.tgdeferrable,
            "tginitdeferred": self.tginitdeferred,
            "whenclause": self.whenclause,
            "prosrc": self.prosrc,
            "description": self.description,
        }
        self._trigger_definition(query_data)
        self._get_trigger_function_and_columns(query_data)

        return {
            "data": query_data,
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

    ##########################################################################
    #
    # pgAdmin 4 - PostgreSQL Tools
    #
    # Copyright (C) 2013 - 2017, The pgAdmin Development Team
    # This software is released under the PostgreSQL Licence
    #
    ##########################################################################

    def _trigger_definition(self, data):
        """
        This function will set the trigger definition details from the raw data
        These include parameters: 'fires', 'is_row_trigger', 'evnt_insert',
        'evnt_delete', 'evnt_update', 'evnt_truncate'

        Args:
            data: Properties data

        Returns:
            Updated properties data with trigger definition
        """

        # Here we are storing trigger definition
        # We will use it to check trigger type definition
        trigger_definition = {
            'TRIGGER_TYPE_ROW': (1 << 0),
            'TRIGGER_TYPE_BEFORE': (1 << 1),
            'TRIGGER_TYPE_INSERT': (1 << 2),
            'TRIGGER_TYPE_DELETE': (1 << 3),
            'TRIGGER_TYPE_UPDATE': (1 << 4),
            'TRIGGER_TYPE_TRUNCATE': (1 << 5),
            'TRIGGER_TYPE_INSTEAD': (1 << 6)
        }

        # Fires event definition
        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_BEFORE']:
            data['fires'] = 'BEFORE'
        elif data['tgtype'] & trigger_definition['TRIGGER_TYPE_INSTEAD']:
            data['fires'] = 'INSTEAD OF'
        else:
            data['fires'] = 'AFTER'

        # Trigger of type definition
        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_ROW']:
            data['is_row_trigger'] = True
        else:
            data['is_row_trigger'] = False

        # Event definition
        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_INSERT']:
            data['evnt_insert'] = True
        else:
            data['evnt_insert'] = False

        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_DELETE']:
            data['evnt_delete'] = True
        else:
            data['evnt_delete'] = False

        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_UPDATE']:
            data['evnt_update'] = True
        else:
            data['evnt_update'] = False

        if data['tgtype'] & trigger_definition['TRIGGER_TYPE_TRUNCATE']:
            data['evnt_truncate'] = True
        else:
            data['evnt_truncate'] = False

        return data

    def _get_trigger_function_and_columns(self, data, show_system_objects=False):
        """
        This function will return trigger function with schema name.
        :param data: Data
        :param show_system_objects: show system object

        Sets 'tfunction', 'tgargs', 'columns' of the data dictionary
        :return:
        """
        # If language is 'edbspl' then trigger function should be
        # 'Inline EDB-SPL' else we will find the trigger function
        # with schema name.
        sql = templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'get_triggerfunctions.sql', self._mxin_server_version),
            self._mxin_macro_root,
            tgfoid=self.tgfoid,
            show_system_objects=show_system_objects
        )

        cols, rows = self.server.connection.execute_dict(sql)

        # Update the trigger function which we have fetched with
        # schema name
        if len(rows) > 0 and 'tfunctions' in rows[0]:
            data['tfunction'] = rows[0]['tfunctions']

        if len(data['custom_tgargs']) > 0:
            # We know that trigger has more than 1 argument, let's join them
            # and convert it to string
            formatted_args = [templating.qt_literal(arg, self.server.connection.connection)
                              for arg in data['custom_tgargs']]
            formatted_args = ', '.join(formatted_args)

            data['tgargs'] = formatted_args
        else:
            data['tgargs'] = None

        if len(data['tgattr']) >= 1:
            columns = ', '.join(data['tgattr'].split(' '))
            data['columns'] = self._get_column_details(columns)

        return data

    def _get_column_details(self, clist):
        """
        This functional will fetch list of column for trigger.
        :param clist:
        :return:
        """
        sql = templating.render_template(
            templating.get_template_path(self._mxin_template_root, 'get_columns.sql', self._mxin_server_version),
            self._mxin_macro_root,
            tid=self.parent.oid,
            clist=clist
        )

        cols, rows = self.server.connection.execute_dict(sql)
        columns = []
        for row in rows:
            columns.append(row['name'])

        return columns
