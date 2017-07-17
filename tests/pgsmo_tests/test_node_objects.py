# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import pgsmo.objects.node_object as node
from pgsmo.utils.querying import ServerConnection
import tests.pgsmo_tests.utils as utils


class TestNodeCollection(unittest.TestCase):
    def test_init(self):
        # Setup: Create a mock generator
        generator = mock.MagicMock()

        # If: I initialize a node collection
        node_collection = node.NodeCollection(generator)

        # Then:
        # ... The internal properties should be set properly
        self.assertIs(node_collection._generator, generator)
        self.assertIsNone(node_collection._items)

        # ... Make sure the generator has not been called
        generator.assert_not_called()

    def test_index_bad_type(self):
        # Setup: Create a mock generator and node collection
        generator = mock.MagicMock()
        node_collection = node.NodeCollection(generator)

        # If: I ask for items with an invalid type for the index
        # Then: I should get an exception
        with self.assertRaises(TypeError):
            node_collection[1.2]

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            node_collection[789]

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(node_collection._items, mock_objects)

    def test_index_no_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching name
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            node_collection['c']

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(node_collection._items, mock_objects)

    def test_index_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that has a matching oid
        output = node_collection[456]

        # Then: The item I have should be the expected item
        self.assertIs(output, mock_objects[1])

    def test_index_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that has a matching name
        output = node_collection['b']

        # Then: The item I have should be the expected item
        self.assertIs(output, mock_objects[1])

    def test_iterator(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I iterate over the items in the collection
        output = [n for n in node_collection]

        # Then: The list should be equivalent to the list of objects
        self.assertListEqual(output, mock_objects)

    def test_len(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I ask for the length of the node collection
        length = len(node_collection)

        # Then: The length should be equal to the length of the objects
        self.assertEqual(length, len(mock_objects))

    def test_reset(self):
        # Setup: Create a mock generator and node collection that has been loaded
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)
        node_collection[123]     # Force the collection to load

        # If: I reset the collection
        node_collection.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(node_collection._items)


class TestNodeLazyPropertyCollection(unittest.TestCase):
    def test_init(self):
        # Setup: Create a mock generator
        generator = mock.MagicMock()

        # If: I initialize a node property collection
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # Then:
        # ... Internal state should be appropriately setup
        self.assertIs(prop_collection._generator, generator)
        self.assertIsNone(prop_collection._items)

        # ... The generator should not have been called
        generator.assert_not_called()

    def test_index_bad_type(self):
        # Setup: Create a mock generator and property collection
        generator = mock.MagicMock()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I ask for items with an invalid type for the index
        # Then: I should get an exception
        with self.assertRaises(TypeError):
            prop_collection[1.2]

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and property collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(KeyError):
            prop_collection['does_not_exist']

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(prop_collection._items, mock_objects)

    def test_index_match(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that exists
        output = prop_collection['prop1']

        # Then: The item should be the expected item
        self.assertEqual(output, mock_objects['prop1'])

    def test_iterator(self):
        # Setup: Create a mock generator and property collection
        generator, mock_results = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I iterate over the items in the collection
        output = [item for item in prop_collection]
        expected_output = [item for item in mock_results]

        # Then: The dictionary I rebuilt from the iteration should match the original dictionary
        self.assertListEqual(output, expected_output)

    def test_len(self):
        # Setup: Create a mock generator and property collection
        generator, mock_results = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get the length of the collection
        output = len(prop_collection)

        # Then: The length should be the same as the length of the objects returned
        self.assertEqual(output, len(mock_results))

    def test_items(self):
        # Setup: Create a mock generator and property collection
        generator, mock_results = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get the items of the collection
        items = prop_collection.items()

        # Then: They should be the same as the items in the results
        self.assertListEqual(list(items), list(mock_results.items()))

    def test_keys(self):
        # Setup: Create a mock generator and property collection
        generator, mock_results = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get the keys of the collection
        keys = prop_collection.keys()

        # Then: They should be the same as the keys in the results
        self.assertListEqual(list(keys), list(mock_results.keys()))

    def test_reset(self):
        # Setup: Create a mock generator and property collection and force it to load
        generator, mock_results = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)
        prop_collection['prop1']    # Force the collection to load

        # If: I reset the collection
        prop_collection.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(prop_collection._items)


class TestNodeObject(unittest.TestCase):
    def test_init(self):
        # If: I create a node object
        conn = ServerConnection(utils.MockConnection(None))
        node_obj = MockNodeObject(conn, 'abc')

        # Then: The properties should be assigned as defined
        self.assertIsNone(node_obj._oid)
        self.assertIsNone(node_obj.oid)

        self.assertEqual(node_obj._name, 'abc')
        self.assertEqual(node_obj.name, 'abc')

        self.assertListEqual(node_obj._child_collections, [])
        self.assertListEqual(node_obj._property_collections, [])

        self.assertIs(node_obj._conn, conn)

    def test_get_nodes(self):
        # Setup:
        # ... Create a mockup of a server connection with a mock executor
        mock_objs = [{'name': 'abc', 'oid': 123}, {'name': 'def', 'oid': 456}]
        mock_executor = mock.MagicMock(return_value=([{}, {}], mock_objs))
        mock_conn = ServerConnection(utils.MockConnection(None, version="10101"))
        mock_conn.execute_dict = mock_executor

        # ... Create a mock template renderer
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Create a mock generator
        mock_output = {}
        mock_generator = mock.MagicMock(return_value=mock_output)

        # ... Do the patching
        with mock.patch('pgsmo.objects.node_object.templating.render_template', mock_render, create=True):
            with mock.patch('pgsmo.objects.node_object.templating.get_template_path', mock_template_path, create=True):
                # If: I ask for a collection of nodes
                kwargs = {'arg1': 'something'}
                nodes = node.get_nodes(mock_conn, 'root', mock_generator, **kwargs)

        # Then:
        # ... The template path should have been called once
        mock_template_path.assert_called_once_with('root', 'nodes.sql', (1, 1, 1))

        # ... The template renderer should have been called once
        mock_render.assert_called_once_with('path', **kwargs)

        # ... A query should have been executed
        mock_executor.assert_called_once_with('SQL')

        # ... The generator should have been called twice with different object props
        mock_generator.assert_any_call(mock_conn, **mock_objs[0])
        mock_generator.assert_any_call(mock_conn, **mock_objs[1])

        # ... The output list of nodes should match what the generator created
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_output, mock_output])

    def test_register_child_collection(self):
        # Setup: Create a node object
        conn = ServerConnection(utils.MockConnection(None))
        node_obj = MockNodeObject(conn, 'obj_name')

        # If: I register a child collection
        generator = mock.MagicMock()
        collection1 = node_obj._register_child_collection(generator)

        # Then
        # ... The returned collection should be a collection with the given generator
        self.assertIsInstance(collection1, node.NodeCollection)
        self.assertIs(collection1._generator, generator)

        # ... The collection should be added to the list of registered collections
        self.assertEqual(len(node_obj._child_collections), 1)
        self.assertIn(collection1, node_obj._child_collections)

        # If: I add another one
        collection2 = node_obj._register_child_collection(generator)

        # Then: The collection should be appended to the list of registered collections
        self.assertEqual(len(node_obj._child_collections), 2)
        self.assertIn(collection1, node_obj._child_collections)
        self.assertIn(collection2, node_obj._child_collections)

    def test_register_property_collection(self):
        # Setup: Create a node object
        conn = ServerConnection(utils.MockConnection(None))
        node_obj = MockNodeObject(conn, 'obj_name')

        # If: I register a property collection
        generator = mock.MagicMock()
        collection1 = node_obj._register_property_collection(generator)

        # Then:
        # ... The returned collection should be a collection with the provided generator
        self.assertIsInstance(collection1, node.NodeLazyPropertyCollection)
        self.assertIs(collection1._generator, generator)

        # ... The collection should be added to the list of registered collections
        self.assertEqual(len(node_obj._property_collections), 1)
        self.assertIn(collection1, node_obj._property_collections)

        # If: I add another one
        collection2 = node_obj._register_property_collection(generator)

        # Then: The collection should be appended to the list of registered collections
        self.assertEqual(len(node_obj._property_collections), 2)
        self.assertIn(collection1, node_obj._property_collections)
        self.assertIn(collection2, node_obj._property_collections)

    def test_refresh(self):
        # Setup:
        # ... Create a node object
        conn = ServerConnection(utils.MockConnection(None))
        node_obj = MockNodeObject(conn, 'obj_name')

        # ... Add a couple child collections
        node_generator = mock.MagicMock()
        collection1 = node.NodeCollection(node_generator)
        collection1.reset = mock.MagicMock()
        collection2 = node.NodeCollection(node_generator)
        collection2.reset = mock.MagicMock()
        node_obj._child_collections = [collection1, collection2]

        # ... Add a couple property collections
        prop_generator = mock.MagicMock()
        props1 = node.NodeLazyPropertyCollection(prop_generator)
        props1.reset = mock.MagicMock()
        props2 = node.NodeLazyPropertyCollection(prop_generator)
        props2.reset = mock.MagicMock()
        node_obj._property_collections = [props1, props2]

        # If: I refresh the object
        node_obj.refresh()

        # Then: The child collections should have been reset
        collection1.reset.assert_called_once()
        collection2.reset.assert_called_once()
        props1.reset.assert_called_once()
        props2.reset.assert_called_once()


class MockNodeObject(node.NodeObject):
    @classmethod
    def _from_node_query(cls, conn: ServerConnection, **kwargs):
        pass

    def __init__(self, conn: ServerConnection, name: str):
        super(MockNodeObject, self).__init__(conn, name)


def _get_mock_node_generator():
    conn = ServerConnection(utils.MockConnection(None))

    mock_object1 = MockNodeObject(conn, 'a')
    mock_object1._oid = 123

    mock_object2 = MockNodeObject(conn, 'b')
    mock_object2._oid = 456

    mock_objects = [mock_object1, mock_object2]
    return mock.MagicMock(return_value=mock_objects), mock_objects


def _get_mock_property_generator():
    mock_results = {
        'prop1': 'value',
        'prop2': 123,
        'prop3': True
    }
    return mock.MagicMock(return_value=mock_results), mock_results
