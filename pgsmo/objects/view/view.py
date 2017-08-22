# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.table_objects import Column, Rule, Trigger
import pgsmo.objects.node_object as node
from pgsmo.objects.server import server as s    # noqa
import pgsmo.utils.templating as templating


class View(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')

    @classmethod
    def _from_node_query(cls, server: 's.Server', parent: node.NodeObject, **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param server: Server that owns the view
        :param parent: Object that is the parent of the view. Should be a Schema
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(server, parent, kwargs['name'])
        view._oid = kwargs['oid']

        return view

    def __init__(self, server: 's.Server', parent: node.NodeObject, name: str):
        super(View, self).__init__(server, parent, name)

        # Declare child items
        self._columns: node.NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._server, self)
        )
        self._rules: node.NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._server, self)
        )
        self._triggers: node.NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._server, self)
        )

    # PROPERTIES ###########################################################
    @property
    def extended_vars(self):
        template_vars = {
            'scid': self.parent.oid
        }
        return template_vars

    # -CHILD OBJECTS #######################################################
    @property
    def columns(self) -> node.NodeCollection[Column]:
        return self._columns

    @property
    def rules(self) -> node.NodeCollection[Rule]:
        return self._rules

    @property
    def triggers(self) -> node.NodeCollection[Trigger]:
        return self._triggers

    # FULL OBJECT PROPERTIES ###############################################
    @property
    def schema(self):
        return self._full_properties.get("schema", "")

    @property
    def definition(self):
        return self._full_properties.get("definition", "")

    @property
    def owner(self):
        return self._full_properties.get("owner", "")

    @property
    def comment(self):
        return self._full_properties.get("comment", "")

    @property
    def nspname(self):
        return self._full_properties.get("nspname", "")

    @property
    def check_option(self):
        return self._full_properties.get("check_option", "")

    @property
    def security_barrier(self):
        return self._full_properties.get("security_barrier", "")

    # METHODS ##############################################################

    def create_script(self) -> str:
        """ Function to retrieve create scripts for a view """
        data = self._create_query_data()
        query_file = "create.sql"
        return self._get_template(query_file, data)

    def delete_script(self) -> str:
        """ Function to retrieve delete scripts for a view """
        data = self._delete_query_data()
        query_file = "delete.sql"
        return self._get_template(query_file, data)

    def update_script(self) -> str:
        """ Function to retrieve update scripts for a view """
        data = self._update_query_data()
        query_file = "update.sql"
        return self._get_template(query_file, data)

    # IMPLEMENTATION DETAILS ################################################
    @classmethod
    def _template_root(cls, server: 's.Server') -> str:
        return cls.TEMPLATE_ROOT

    # HELPER METHODS #######################################################

    def _create_query_data(self) -> dict:
        """ Provides data input for create script """
        data = {
            "data": {
                "name": self.name,
                "schema": self.parent.name,
                "definition": self.definition,
                "check_option": self.check_option,
                "security_barrier": self.security_barrier
            }}
        return data

    def _delete_query_data(self) -> dict:
        """ Provides data input for delete script """
        data = {
            "vid": self._oid,
            "name": self.name,
            "nspname": self.nspname
        }
        return data

    def _update_query_data(self) -> dict:
        """ Provides data input for update script """
        data = {"data": {}}
        return data
