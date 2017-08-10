# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
from typing import Optional

import pgsmo.objects.node_object as node
from pgsmo.objects.collation import Collation
from pgsmo.objects.functions import Function, TriggerFunction
from pgsmo.objects.sequence import Sequence
from pgsmo.objects.server import server as s    # noqa
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
import pgsmo.utils.templating as templating
import pgsmo.utils.querying as querying


TEMPLATE_ROOT = templating.get_template_root(__file__, 'templates')
MACRO_ROOT = templating.get_template_root(__file__, 'macros')


class Schema(node.NodeObject):
    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'Schema':
        """
        Creates an instance of a schema object from the results of a nodes query
        :param server: Server that owns the schema
        :param parent: Parent object of the schema. Should be a Database
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the schema
            oid int: Object ID of the schema
            can_create bool: Whether or not the schema can be created by the current user
            has_usage bool: Whether or not the schema can be used(?)
        :return:
        """
        schema = cls(server, parent, kwargs['name'])
        schema._oid = kwargs['oid']
        schema._can_create = kwargs['can_create']
        schema._has_usage = kwargs['has_usage']

        return schema

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(Schema, self).__init__(server, parent, name)

        # Declare the optional parameters
        self._can_create: Optional[bool] = None
        self._has_usage: Optional[bool] = None

        # Declare the child items
        self._collations: node.NodeCollection = self._register_child_collection(
            lambda: Collation.get_nodes_for_parent(self._server, self)
        )
        self._functions: node.NodeCollection = self._register_child_collection(
            lambda: Function.get_nodes_for_parent(self._server, self)
        )
        self._sequences: node.NodeCollection = self._register_child_collection(
            lambda: Sequence.get_nodes_for_parent(self._server, self)
        )
        self._tables: node.NodeCollection = self._register_child_collection(
            lambda: Table.get_nodes_for_parent(self._server, self)
        )
        self._trigger_functions = self._register_child_collection(
            lambda: TriggerFunction.get_nodes_for_parent(self._server, self)
        )
        self._views: node.NodeCollection = self._register_child_collection(
            lambda: View.get_nodes_for_parent(self._server, self)
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
    def collations(self) -> node.NodeCollection:
        return self._collations

    @property
    def functions(self) -> node.NodeCollection:
        return self._functions

    @property
    def sequences(self) -> node.NodeCollection:
        return self._sequences

    @property
    def tables(self) -> node.NodeCollection:
        return self._tables

    @property
    def trigger_functions(self) -> node.NodeCollection:
        return self._trigger_functions

    @property
    def views(self) -> node.NodeCollection:
        return self._views

    @property
    def namespaceowner(self):
        return self._full_properties.get("namespaceowner", "")

    @property
    def description(self):
        return self._full_properties.get("description", "")

    @property
    def nspacl(self):
        return self._full_properties.get("nspacl", "")

    @property
    def seclabels(self):
        return self._full_properties.get("seclabels", "")

    @property
    def cascade(self):
        return self._full_properties.get("cascade", "")

    @property
    def defacl(self):
        return self._full_properties.get("defacl", "")

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return path.join(TEMPLATE_ROOT, server.server_type)

    @classmethod
    def _macro_root(cls) -> str:
        return [MACRO_ROOT]

    # SCRIPTING METHODS ##############################################################
    def create_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve create scripts for a schema """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(connection, query_file, data, paths_to_add=self._macro_root())

    def delete_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve delete scripts for schema """
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(connection, query_file, data)

    def update_script(self, connection: querying.ServerConnection) -> str:
        """ Function to retrieve update scripts for schema """
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(connection, query_file, data, paths_to_add=self._macro_root())

    #  HELPER METHODS ######################################################
    def _create_query_data(self) -> dict:
        """ Function that returns data for create script """
        data = {"data": {
            "name": self.name,
            "namespaceowner": self.namespaceowner,
            "description": self.description,
            "nspacl": self.nspacl,
            "seclabels": self.seclabels
        }}
        return data

    def _delete_query_data(self) -> dict:
        """ Function that returns data for delete script """
        data = {
            "name": self.name,
            "cascade": self.cascade
        }
        return data

    def _update_query_data(self) -> dict:
        """ Function that returns data for update script """
        data = {
            "data": {
                "name": self.name,
                "namespaceowner": self.namespaceowner,
                "description": self.description,
                "nspacl": self.nspacl,
                "defacl": self.defacl,
                "seclabels": self.seclabels
            }, "o_data": {
                "name": "",
                "namespaceowner": "",
                "description": ""
            }
        }
        return data
