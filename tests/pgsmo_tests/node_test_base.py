# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
import os.path
from typing import Callable, List, Mapping, Type
import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeCollection, NodeLazyPropertyCollection, NodeObject
from pgsmo.objects.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate
from pgsmo.objects.server.server import Server
import tests.pgsmo_tests.utils as utils


class NodeObjectTestBase(metaclass=ABCMeta):
    unittest = unittest.TestCase('__init__')

    @property
    @abstractmethod
    def basic_properties(self) -> Mapping[str, any]:
        pass

    @property
    @abstractmethod
    def class_for_test(self) -> Type[NodeObject]:
        pass

    @property
    @abstractmethod
    def collections(self) -> List[str]:
        pass

    @property
    def full_properties(self) -> Mapping[str, str]:
        return {}

    @property
    def init_lambda(self) -> Callable[[Server, NodeObject, str], NodeObject]:
        class_ = self.class_for_test
        return lambda server, parent, name: class_(server, parent, name)

    @property
    @abstractmethod
    def node_query(self) -> dict:
        pass

    @property
    def property_query(self) -> dict:
        return {}

    @property
    def parent_expected_to_be_none(self) -> bool:
        return False

    # TEST METHODS #########################################################
    def test_from_node_query(self):
        # If: I create a new object from a node row with the expected parent type
        mock_server = Server(utils.MockConnection(None))
        mock_parent = utils.MockNodeObject(mock_server, None, 'parent') if not self.parent_expected_to_be_none else None
        obj = self.class_for_test._from_node_query(mock_server, mock_parent, **self.node_query)

        # Then:
        # ... The returned object must be an instance of the class
        NodeObjectTestBase.unittest.assertIsInstance(obj, NodeObject)
        NodeObjectTestBase.unittest.assertIsInstance(obj, self.class_for_test)

        # ... Validate the node object properties
        utils.assert_threeway_equals(mock_server, obj._server, obj.server)
        utils.assert_threeway_equals(self.node_query['oid'], obj._oid, obj.oid)
        utils.assert_threeway_equals(self.node_query['name'], obj._name, obj.name)

        # ... Validate the basic properties
        for attr, value in self.basic_properties.items():
            NodeObjectTestBase.unittest.assertEqual(getattr(obj, attr), value)

        # ... Validate the collections
        for attr in self.collections:
            NodeObjectTestBase.unittest.assertIsInstance(getattr(obj, attr), NodeCollection)

        # ... Call the validation function
        self._custom_validate_from_node(obj, mock_server)

    def test_full_properties(self):
        # Setup:
        # NOTE: We're *not* mocking out the template rendering b/c this will verify that there's a template
        # ... Create a mock query execution that will return the properties
        mock_exec_dict = mock.MagicMock(return_value=([], [self.property_query]))

        # ... Create an instance of the class
        mock_server = Server(utils.MockConnection(None))
        mock_server.connection.execute_dict = mock_exec_dict
        mock_grand_parent = utils.MockNodeObject(mock_server, None, 'grandparent') if not self.parent_expected_to_be_none else None
        mock_parent = utils.MockNodeObject(mock_server, mock_grand_parent, 'parent') if not self.parent_expected_to_be_none else None
        name = 'test'
        obj = self.init_lambda(mock_server, mock_parent, name)

        self._full_properties_helper(obj, mock_server)

    def test_init(self):
        # If: I create an instance of the provided class
        mock_server = Server(utils.MockConnection(None))
        mock_parent = utils.MockNodeObject(mock_server, None, 'parent') if not self.parent_expected_to_be_none else None
        name = 'test'
        obj = self.init_lambda(mock_server, mock_parent, name)

        # Then:
        # ... Perform the init validation
        # noinspection PyTypeChecker
        self._init_validation(obj, mock_server, mock_parent, name)

        # ... Call the custom validation function
        self._custom_validate_init(obj, mock_server)

    def test_template_path_pg(self):
        # Setup: Create a mock connection that has PG as the server type
        mock_server = Server(utils.MockConnection(None))
        mock_server._ServerConnection__server_type = mock.MagicMock(return_value='pg')

        # If: I ask for the template path of the class
        path = self.class_for_test._template_root(mock_server)

        # Then: The path should be a string that exists
        NodeObjectTestBase.unittest.assertIsInstance(path, str)
        NodeObjectTestBase.unittest.assertTrue(os.path.exists(path))

    # TODO: Disabled 08/23/2017 beruss -- reenable once properties are fixed, tracked by https://github.com/Microsoft/carbon/issues/1734
    def _test_scripting_mixins(self):
        # Setup: Create an instance of the object
        mock_server = Server(utils.MockConnection(None))
        mock_grand_parent = utils.MockNodeObject(mock_server, None, 'grandparent') if not self.parent_expected_to_be_none else None
        mock_parent = utils.MockNodeObject(mock_server, mock_grand_parent, 'parent') if not self.parent_expected_to_be_none else None
        name = 'test'
        obj = self.init_lambda(mock_server, mock_parent, name)
        obj._full_properties = self.property_query

        if isinstance(obj, ScriptableCreate):
            # If: I script for create
            script = obj.create_script()

            # Then: The script should successfully return
            utils.assert_is_not_none_or_whitespace(script)

        if isinstance(obj, ScriptableDelete):
            # If: I script for delete
            script = obj.delete_script()

            # Then: The script should successfully return
            utils.assert_is_not_none_or_whitespace(script)

        if isinstance(obj, ScriptableUpdate):
            # If: I script for update
            script = obj.update_script()

            # Then: The script should successfully return
            utils.assert_is_not_none_or_whitespace(script)

    # TODO: Add test for PPAS server type when we support it

    # CUSTOM TEST LOGIC ####################################################
    @staticmethod
    def _custom_validate_from_node(obj, mock_server: Server):
        """
        Can be overridden in child classes to add custom validation to _from_node_query tests after
        the standard validation is performed.
        """
        pass

    @staticmethod
    def _custom_validate_init(obj, mock_server: Server):
        """
        Can be overridden in child classes to add custom validation to __init__ tests after the
        standard validation is performed.
        """
        pass

    # PROTECTED HELPERS ####################################################
    def _init_validation(self, obj: NodeObject, mock_server: Server, mock_parent: NodeObject, name: str):
        """
        Default init validation that can be reused in overrides of test_init
        """
        # ... The object must be of the type that was provided
        test_case = unittest.TestCase('__init__')
        test_case.assertIsInstance(obj, NodeObject)
        test_case.assertIsInstance(obj, self.class_for_test)

        # ... The NodeObject basic properties should be set up appropriately
        utils.assert_threeway_equals(mock_server, obj._server, obj.server)
        utils.assert_threeway_equals(None, obj._oid, obj.oid)
        utils.assert_threeway_equals(name, obj._name, obj.name)
        utils.assert_threeway_equals(mock_parent, obj._parent, obj.parent)

        # ... The rest of the properties should be none
        for prop in self.basic_properties.keys():
            test_case.assertIsNone(getattr(obj, prop))

        # ... The full properties collection should be a lazy property collection
        test_case.assertIsInstance(obj._full_properties, NodeLazyPropertyCollection)

        # ... The child node collections should be assigned to node collections
        for coll in self.collections:
            test_case.assertIsInstance(getattr(obj, coll), NodeCollection)

        # We won't test the full properties here because it'll run the generator
        # and setting up the mocking is annoying in this case

    def _full_properties_helper(self, obj, mock_server: Server):
        # If: I retrieve all the values in the full properties
        # Then:
        # ... The properties based on the properties query should be available
        for prop, key in self.full_properties.items():
            NodeObjectTestBase.unittest.assertEqual(getattr(obj, prop), self.property_query[key])

        # ... The generator should have been called once
        if len(self.full_properties) > 1:
            mock_server.connection.execute_dict.assert_called_once()
