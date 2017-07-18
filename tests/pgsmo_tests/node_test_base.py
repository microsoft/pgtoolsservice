# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod
import os.path
from typing import List, Mapping
import unittest
import unittest.mock as mock

from pgsmo.objects.node_object import NodeCollection, NodeObject
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


class NodeObjectTestBase(metaclass=ABCMeta):
    unittest = unittest.TestCase('__init__')

    @property
    @abstractmethod
    def basic_properties(self) -> Mapping[str, any]:
        pass

    @property
    @abstractmethod
    def class_for_test(self):
        pass

    @property
    @abstractmethod
    def collections(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def node_query(self) -> dict:
        pass

    # TEST METHODS #########################################################
    def test_from_node_query(self):
        # If: I create a new object from a node row
        mock_conn = ServerConnection(utils.MockConnection(None))
        obj = self.class_for_test._from_node_query(mock_conn, **self.node_query)

        # Then:
        # ... The returned object must be an instance of the class
        NodeObjectTestBase.test_case = unittest.TestCase('__init__')
        NodeObjectTestBase.test_case.assertIsInstance(obj, NodeObject)
        NodeObjectTestBase.test_case.assertIsInstance(obj, self.class_for_test)

        # ... Validate the node object properties
        NodeObjectTestBase.test_case.assertIs(obj._conn, mock_conn)
        NodeObjectTestBase.test_case.assertEqual(obj._oid, self.node_query['oid'])
        NodeObjectTestBase.test_case.assertEqual(obj.oid, self.node_query['oid'])
        NodeObjectTestBase.test_case.assertEqual(obj._name, self.node_query['name'])
        NodeObjectTestBase.test_case.assertEqual(obj.name, self.node_query['name'])

        # ... Validate the basic properties
        for attr, value in self.basic_properties.items():
            NodeObjectTestBase.test_case.assertEqual(getattr(obj, attr), value)

        # ... Validate the collections
        for attr in self.collections:
            NodeObjectTestBase.test_case.assertIsInstance(getattr(obj, attr), NodeCollection)

        # ... Call the validation function
        self._custom_validate_from_node(obj, mock_conn)

    def test_init(self):
        # If: I create an instance of the provided class
        mock_conn = ServerConnection(utils.MockConnection(None))
        name = 'test'
        class_ = self.class_for_test
        obj = class_(mock_conn, name)

        # Then:
        # ... Perform the init validation
        self._init_validation(obj, mock_conn, name)

        # ... Call the custom validation funtion
        self._custom_validate_init(obj, mock_conn)

    def test_template_path_pg(self):
        # Setup: Create a mock connection that has PG as the server type
        mock_conn = ServerConnection(utils.MockConnection(None))
        mock_conn._ServerConnection__server_type = mock.MagicMock(return_value='pg')

        # If: I ask for the template path of the class
        path = self.class_for_test._template_root(mock_conn)

        # Then: The path should be a string that exists
        NodeObjectTestBase.unittest.assertIsInstance(path, str)
        NodeObjectTestBase.unittest.assertTrue(os.path.exists(path))

    # TODO: Add test for PPAS server type when we support it

    # CUSTOM TEST LOGIC ####################################################
    def _custom_validate_from_node(self, obj, mock_conn: ServerConnection):
        """
        Can be overridden in child classes to add custom validation to _from_node_query tests after
        the standard validation is performed.
        """
        pass

    def _custom_validate_init(self, obj, mock_conn: ServerConnection):
        """
        Can be overridden in child classes to add custom vaidation to __init__ tests after the
        standard validation is performed.
        """
        pass

    # PROTECTED HELPERS ####################################################
    def _init_validation(self, obj, mock_conn: ServerConnection, name: str):
        """
        Default init validation that can be reused in overrides of test_init
        """
        # ... The object must be of the type that was provided
        test_case = unittest.TestCase('__init__')
        test_case.assertIsInstance(obj, NodeObject)
        test_case.assertIsInstance(obj, self.class_for_test)

        # ... The NodeObject basic properties should be set up appropriately
        test_case.assertIs(obj._conn, mock_conn)
        test_case.assertEqual(obj._name, name)
        test_case.assertEqual(obj.name, name)
        test_case.assertIsNone(obj._oid)
        test_case.assertIsNone(obj.oid)

        # ... The rest of the properties should be none
        for prop in self.basic_properties.keys():
            test_case.assertIsNone(getattr(obj, prop))

        # ... The child properties should be assigned to node collections
        for coll in self.collections:
            test_case.assertIsInstance(getattr(obj, coll), NodeCollection)
