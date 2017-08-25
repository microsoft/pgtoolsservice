# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import pgsmo.objects.node_object as node
from pgsmo.objects.server.server import Server
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
        self.assertIsNone(node_collection._items_impl)

    def test_items_loaded(self):
        # Setup: Create a mock generator and node collection, mock that it's loaded
        generator = mock.MagicMock()
        node_collection = node.NodeCollection(generator)
        node_collection._items_impl = {}

        # If: I access the items property
        output = node_collection._items

        # Then: The generator should not have been called
        generator.assert_not_called()
        self.assertIs(output, node_collection._items_impl)

    def test_items_not_loaded(self):
        # Setup: Create a mock generator and node collection
        generator = mock.MagicMock(return_value={})
        node_collection = node.NodeCollection(generator)

        # If: I access the items property
        output = node_collection._items

        # Then: The generator should have been called
        generator.assert_called_once()
        self.assertIs(output, node_collection._items_impl)

        # ... Make sure the generator has not been called
        generator.assert_called_once()

    def test_index_bad_type(self):
        # Setup: Create a mock generator and node collection
        generator = mock.MagicMock()
        node_collection = node.NodeCollection(generator)

        # If: I ask for items with an invalid type for the index
        # Then: I should get an exception
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            obj = node_collection[1.2]      # noqa

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            obj = node_collection[789]      # noqa

    def test_index_no_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_node_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching name
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            obj = node_collection['c']      # noqa

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
        obj = node_collection[123]     # noqa

        # If: I reset the collection
        node_collection.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(node_collection._items_impl)


class TestNodeLazyPropertyCollection(unittest.TestCase):
    def test_init(self):
        # Setup: Create a mock generator
        generator = mock.MagicMock()

        # If: I initialize a node property collection
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # Then:
        # ... Internal state should be appropriately setup
        self.assertIs(prop_collection._generator, generator)
        self.assertIsNone(prop_collection._items_impl)

        # ... The generator should not have been called
        generator.assert_not_called()

    def test_items_loaded(self):
        # Setup: Create a mock generator, property collection and mock that it's loaded
        generator = mock.MagicMock()
        prop_collection = node.NodeLazyPropertyCollection(generator)
        prop_collection._items_impl = {}

        # If: I look at the list of items after they
        output = prop_collection._items

        # Then: The generator should not have been called
        generator.assert_not_called()
        self.assertIs(output, prop_collection._items_impl)

    def test_items_not_loaded(self):
        # Setup: Create a mock generator, property collection
        generator = mock.MagicMock(return_value={})
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I look at the list of items after they
        output = prop_collection._items

        # Then: The generator should have been called
        generator.assert_called_once()
        self.assertIs(output, prop_collection._items_impl)

    def test_index_bad_type(self):
        # Setup: Create a mock generator and property collection
        generator = mock.MagicMock()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I ask for items with an invalid type for the index
        # Then:
        # ... I should get an exception
        with self.assertRaises(TypeError):
            # noinspection PyTypeChecker
            obj = prop_collection[1.2]      # noqa

        # ... The generator should not have been called
        generator.assert_not_called()

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and property collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(KeyError):
            obj = prop_collection['does_not_exist']     # noqa

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

    def test_get_no_match_no_default(self):
        # Setup: Create a mock generator and property collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that doesn't exist and do not provide a default
        output = prop_collection.get('does_not_exist')

        # Then: dict.get default should be returned
        self.assertEqual(output, prop_collection._items.get('does_not_exist'))

    def test_get_no_match_with_default(self):
        # Setup: Create a mock generator and property collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that doesn't exist and provide a default
        output = prop_collection.get('does_not_exist', 'default')

        # Then: dict.get default should be returned
        self.assertEqual(output, prop_collection._items.get('does_not_exist', 'default'))

    def test_get_has_match(self):
        # Setup: Create a mock generator and property collection
        generator, mock_objects = _get_mock_property_generator()
        prop_collection = node.NodeLazyPropertyCollection(generator)

        # If: I get an item that does exist
        output = prop_collection.get('prop1')

        # Then: dict.get default should be returned
        self.assertEqual(output, prop_collection._items.get('prop1'))

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
        obj = prop_collection['prop1']    # Force the collection to load    # noqa

        # If: I reset the collection
        prop_collection.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(prop_collection._items_impl)


class TestNodeObject(unittest.TestCase):
    def test_init(self):
        # If: I create a node object
        server = Server(utils.MockConnection(None))
        parent = utils.MockNodeObject(server, None, 'parent')
        node_obj = utils.MockNodeObject(server, parent, 'abc')

        # Then: The properties should be assigned as defined
        utils.assert_threeway_equals(None, node_obj._oid, node_obj.oid)
        utils.assert_threeway_equals('abc', node_obj._name, node_obj.name)
        utils.assert_threeway_equals(server, node_obj._server, node_obj.server)
        utils.assert_threeway_equals(parent, node_obj._parent, node_obj.parent)

        self.assertListEqual(node_obj._child_collections, [])
        self.assertEqual(len(node_obj._property_collections), 1)

        self.assertIsInstance(node_obj._full_properties, node.NodeLazyPropertyCollection)
        self.assertEqual(node_obj._full_properties._generator, node_obj._property_generator)

    def test_get_nodes_for_parent_no_parent(self):
        # Setup:
        # ... Create a server connection that will return some mock node rows
        mock_server, mock_executor, mock_objs = _get_node_for_parents_mock_connection()

        # ... Create a mock _from_node generator (so we can validate calls)
        mock_obj = {}
        mock_from_node = mock.MagicMock(return_value=mock_obj)

        # ... Create a mock template rendered
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Patch the template rendering, and the _from_node_query
        patch_render_template = 'pgsmo.objects.node_object.templating.render_template'
        patch_template_path = 'pgsmo.objects.node_object.templating.get_template_path'
        patch_from_node_query = 'tests.pgsmo_tests.utils.MockNodeObject._from_node_query'
        with mock.patch(patch_render_template, mock_render, create=True):
            with mock.patch(patch_template_path, mock_template_path, create=True):
                with mock.patch(patch_from_node_query, mock_from_node, create=True):
                    # If: I ask for a collection of nodes *without a parent object*
                    nodes = utils.MockNodeObject.get_nodes_for_parent(mock_server, None)

        # Then:
        # ... The template path and template renderer should have been called once
        mock_template_path.assert_called_once_with('template_root', 'nodes.sql', mock_server.version)
        mock_render.assert_called_once_with('path', macro_roots=None, **{})     # Params to the renderer should be empty

        # ... A query should have been executed
        mock_executor.assert_called_once_with('SQL')

        # ... The _from_node should have been called twice with the results of the query
        mock_from_node.assert_any_call(mock_server, None, **mock_objs[0])
        mock_from_node.assert_any_call(mock_server, None, **mock_objs[1])

        # ... The output should be a list of objects the _from_node returned
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_obj, mock_obj])

    def test_get_nodes_for_parent_with_parent(self):
        # Setup:
        # ... Create a server connection that will return some mock node rows
        mock_server, mock_executor, mock_objs = _get_node_for_parents_mock_connection()

        # ... Create a mock _from_node generator (so we can validate calls)
        mock_obj = {}
        mock_from_node = mock.MagicMock(return_value=mock_obj)

        # ... Create a mock template rendered
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Create an object that will be the parent of these nodes
        parent = utils.MockNodeObject(mock_server, None, 'parent')
        parent._oid = 123

        # ... Patch the template rendering, and the _from_node_query
        patch_render_template = 'pgsmo.objects.node_object.templating.render_template'
        patch_template_path = 'pgsmo.objects.node_object.templating.get_template_path'
        patch_from_node_query = 'tests.pgsmo_tests.utils.MockNodeObject._from_node_query'
        with mock.patch(patch_render_template, mock_render, create=True):
            with mock.patch(patch_template_path, mock_template_path, create=True):
                with mock.patch(patch_from_node_query, mock_from_node, create=True):
                    # If: I ask for a collection of nodes *with a parent object*
                    nodes = utils.MockNodeObject.get_nodes_for_parent(mock_server, parent)

        # Then:
        # ... The template path and template renderer should have been called once
        mock_template_path.assert_called_once_with('template_root', 'nodes.sql', mock_server.version)
        mock_render.assert_called_once_with('path', macro_roots=None, **{'parent_id': 123})

        # ... A query should have been executed
        mock_executor.assert_called_once_with('SQL')

        # ... The _from_node should have been called twice with the results of the query
        mock_from_node.assert_any_call(mock_server, parent, **mock_objs[0])
        mock_from_node.assert_any_call(mock_server, parent, **mock_objs[1])

        # ... The output should be a list of objects the _from_node returned
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_obj, mock_obj])

    def test_register_child_collection(self):
        # Setup: Create a node object
        server = Server(utils.MockConnection(None))
        node_obj = utils.MockNodeObject(server, None, 'obj_name')

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
        server = Server(utils.MockConnection(None))
        node_obj = utils.MockNodeObject(server, None, 'obj_name')

        # If: I register a property collection
        generator = mock.MagicMock()
        collection1 = node_obj._register_property_collection(generator)

        # Then:
        # ... The returned collection should be a collection with the provided generator
        self.assertIsInstance(collection1, node.NodeLazyPropertyCollection)
        self.assertIs(collection1._generator, generator)

        # ... The collection should be added to the list of registered collections
        self.assertEqual(len(node_obj._property_collections), 2)
        self.assertIn(collection1, node_obj._property_collections)

        # If: I add another one
        collection2 = node_obj._register_property_collection(generator)

        # Then: The collection should be appended to the list of registered collections
        self.assertEqual(len(node_obj._property_collections), 3)
        self.assertIn(collection1, node_obj._property_collections)
        self.assertIn(collection2, node_obj._property_collections)

    def test_refresh(self):
        # Setup:
        # ... Create a node object
        server = Server(utils.MockConnection(None))
        node_obj = utils.MockNodeObject(server, None, 'obj_name')

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
        # noinspection PyUnresolvedReferences
        collection1.reset.assert_called_once()
        # noinspection PyUnresolvedReferences
        collection2.reset.assert_called_once()
        props1.reset.assert_called_once()
        props2.reset.assert_called_once()


def _get_node_for_parents_mock_connection():
    # ... Create a mockup of a server connection with a mock executor
    mock_objs = [{'name': 'abc', 'oid': 123}, {'name': 'def', 'oid': 456}]
    mock_executor = mock.MagicMock(return_value=([{}, {}], mock_objs))
    mock_server = Server(utils.MockConnection(None, version="10101"))
    mock_server.connection.execute_dict = mock_executor

    return mock_server, mock_executor, mock_objs


def _get_mock_node_generator():
    conn = utils.MockConnection(None)

    mock_object1 = utils.MockNodeObject(conn, None, 'a')
    mock_object1._oid = 123

    mock_object2 = utils.MockNodeObject(conn, None, 'b')
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
