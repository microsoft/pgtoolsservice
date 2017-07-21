# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pgsmo.objects.table_objects import Column, Rule, Trigger
import pgsmo.objects.node_object as node
import pgsmo.utils.querying as querying
import pgsmo.utils.templating as templating


class View(node.NodeObject):
    TEMPLATE_ROOT = templating.get_template_root(__file__, 'view_templates')

    @classmethod
    def _from_node_query(cls, conn: querying.ServerConnection, **kwargs) -> 'View':
        """
        Creates a view object from the results of a node query
        :param conn: Connection used to execute the nodes query
        :param kwargs: A row from the nodes query
        Kwargs:
            name str: Name of the view
            oid int: Object ID of the view
        :return: A view instance
        """
        view = cls(conn, kwargs['name'])
        view._oid = kwargs['oid']

        return view

    def __init__(self, conn: querying.ServerConnection, name: str):
        super(View, self).__init__(conn, name)

        # Declare child items
        self._columns: node.NodeCollection[Column] = self._register_child_collection(
            lambda: Column.get_nodes_for_parent(self._conn, self)
        )
        self._rules: node.NodeCollection[Rule] = self._register_child_collection(
            lambda: Rule.get_nodes_for_parent(self._conn, self)
        )
        self._triggers: node.NodeCollection[Trigger] = self._register_child_collection(
            lambda: Trigger.get_nodes_for_parent(self._conn, self)
        )

    # PROPERTIES ###########################################################
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

    @property
    def schema(self):
        return self._full_properties["schema"]

    @property
    def definition(self):
        return self._full_properties["definition"]

    @property
    def owner(self):
        return self._full_properties["owner"]

    @property
    def comment(self):
        return self._full_properties["comment"]

    # HELPER METHODS #######################################################

    def create_query_data(self, connection: querying.ServerConnection) -> dict:

        data = {"data": {
            "name": self._name,
            "schema": self.schema,
            "definition": self.definition,
            "owner": self.owner,
            "comment": self.comment
        }}
        return data

    # METHODS ##############################################################

    def create(self, connection: querying.ServerConnection):
        data = self.create_query_data(connection)
        template_root = self._template_root(connection)
        template_path = templating.get_template_path(template_root, 'create.sql', connection.version)
        create_template = templating.render_template(template_path, **data)
        return create_template

    def update(self):
        pass

    def delete(self):
        pass

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _template_root(cls, conn: querying.ServerConnection) -> str:
        return cls.TEMPLATE_ROOT

    @classmethod
    def get_type(self):
        return "view"
