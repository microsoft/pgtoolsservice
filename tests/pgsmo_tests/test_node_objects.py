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

        # Then: The internal properties should be set properly
        self.assertIs(node_collection._generator, generator)
        self.assertIsNone(node_collection._items)

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
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            obj = node_collection[789]      # noqa

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(node_collection._items, mock_objects)

    def test_index_no_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that doesn't have a matching name
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            obj = node_collection['c']      # noqa

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(node_collection._items, mock_objects)

    def test_index_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that has a matching oid
        output = node_collection[456]

        # Then: The item I have should be the expected item
        self.assertIs(output, mock_objects[1])

    def test_index_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I get an item that has a matching name
        output = node_collection['b']

        # Then: The item I have should be the expected item
        self.assertIs(output, mock_objects[1])

    def test_iterator(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I iterate over the items in the collection
        output = [n for n in node_collection]

        # Then: The list should be equivalent to the list of objects
        self.assertListEqual(output, mock_objects)

    def test_len(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)

        # If: I ask for the length of the node collection
        length = len(node_collection)

        # Then: The length should be equal to the length of the objects
        self.assertEqual(length, len(mock_objects))

    def test_reset(self):
        # Setup: Create a mock generator and node collection that has been loaded
        generator, mock_objects = _get_mock_generator()
        node_collection = node.NodeCollection(generator)
        obj = node_collection[123]     # noqa

        # If: I reset the collection
        node_collection.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(node_collection._items)


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

        self.assertIs(node_obj._conn, conn)

    def test_get_nodes_for_parent_no_parent(self):
        # Setup:
        # ... Create a server connection that will return some mock node rows
        mock_conn, mock_executor, mock_objs = _get_node_for_parents_mock_connection()

        # ... Create a mock _from_node generator (so we can validate calls)
        mock_obj = {}
        mock_from_node = mock.MagicMock(return_value=mock_obj)

        # ... Create a mock template rendered
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Patch the template rendering, and the _from_node_query
        patch_render_template = 'pgsmo.objects.node_object.templating.render_template'
        patch_template_path = 'pgsmo.objects.node_object.templating.get_template_path'
        patch_from_node_query = 'tests.pgsmo_tests.test_node_objects.MockNodeObject._from_node_query'
        with mock.patch(patch_render_template, mock_render, create=True):
            with mock.patch(patch_template_path, mock_template_path, create=True):
                with mock.patch(patch_from_node_query, mock_from_node, create=True):
                    # If: I ask for a collection of nodes *without a parent object*
                    nodes = MockNodeObject.get_nodes_for_parent(mock_conn, None)

        # Then:
        # ... The template path and template renderer should have been called once
        mock_template_path.assert_called_once_with('template_root', 'nodes.sql', mock_conn.version)
        mock_render.assert_called_once_with('path', **{})     # Params to the renderer should be empty

        # ... A query should have been executed
        mock_executor.assert_called_once_with('SQL')

        # ... The _from_node should have been called twice with the results of the query
        mock_from_node.assert_any_call(mock_conn, **mock_objs[0])
        mock_from_node.assert_any_call(mock_conn, **mock_objs[1])

        # ... The output should be a list of objects the _from_node returned
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_obj, mock_obj])

    def test_get_nodes_for_parent_with_parent(self):
        # Setup:
        # ... Create a server connection that will return some mock node rows
        mock_conn, mock_executor, mock_objs = _get_node_for_parents_mock_connection()

        # ... Create a mock _from_node generator (so we can validate calls)
        mock_obj = {}
        mock_from_node = mock.MagicMock(return_value=mock_obj)

        # ... Create a mock template rendered
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Create an object that will be the parent of these nodes
        parent = MockNodeObject(mock_conn, 'parent')
        parent._oid = 123

        # ... Patch the template rendering, and the _from_node_query
        patch_render_template = 'pgsmo.objects.node_object.templating.render_template'
        patch_template_path = 'pgsmo.objects.node_object.templating.get_template_path'
        patch_from_node_query = 'tests.pgsmo_tests.test_node_objects.MockNodeObject._from_node_query'
        with mock.patch(patch_render_template, mock_render, create=True):
            with mock.patch(patch_template_path, mock_template_path, create=True):
                with mock.patch(patch_from_node_query, mock_from_node, create=True):
                    # If: I ask for a collection of nodes *with a parent object*
                    nodes = MockNodeObject.get_nodes_for_parent(mock_conn, parent)

        # Then:
        # ... The template path and template renderer should have been called once
        mock_template_path.assert_called_once_with('template_root', 'nodes.sql', mock_conn.version)
        mock_render.assert_called_once_with('path', **{'parent_id': 123})

        # ... A query should have been executed
        mock_executor.assert_called_once_with('SQL')

        # ... The _from_node should have been called twice with the results of the query
        mock_from_node.assert_any_call(mock_conn, **mock_objs[0])
        mock_from_node.assert_any_call(mock_conn, **mock_objs[1])

        # ... The output should be a list of objects the _from_node returned
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_obj, mock_obj])

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

    def test_refresh(self):
        # Setup: Create a node object with a couple child collections
        conn = ServerConnection(utils.MockConnection(None))
        node_obj = MockNodeObject(conn, 'obj_name')
        generator = mock.MagicMock()
        collection1 = node.NodeCollection(generator)
        collection1.reset = mock.MagicMock()
        collection2 = node.NodeCollection(generator)
        collection2.reset = mock.MagicMock()
        node_obj._child_collections = [collection1, collection2]

        # If: I refresh the object
        node_obj.refresh()

        # Then: The child collections should have been reset
        # noinspection PyUnresolvedReferences
        collection1.reset.assert_called_once()
        # noinspection PyUnresolvedReferences
        collection2.reset.assert_called_once()


class MockNodeObject(node.NodeObject):
    @classmethod
    def _from_node_query(cls, conn: ServerConnection, **kwargs):
        pass

    def __init__(self, conn: ServerConnection, name: str):
        super(MockNodeObject, self).__init__(conn, name)

    @classmethod
    def _template_root(cls, conn: ServerConnection):
        return 'template_root'


def _get_node_for_parents_mock_connection():
    # ... Create a mockup of a server connection with a mock executor
    mock_objs = [{'name': 'abc', 'oid': 123}, {'name': 'def', 'oid': 456}]
    mock_executor = mock.MagicMock(return_value=([{}, {}], mock_objs))
    mock_conn = ServerConnection(utils.MockConnection(None, version="10101"))
    mock_conn.execute_dict = mock_executor

    return mock_conn, mock_executor, mock_objs


def _get_mock_generator():
    conn = ServerConnection(utils.MockConnection(None))

    mock_object1 = MockNodeObject(conn, 'a')
    mock_object1._oid = 123

    mock_object2 = MockNodeObject(conn, 'b')
    mock_object2._oid = 456

    mock_objects = [mock_object1, mock_object2]
    return mock.MagicMock(return_value=mock_objects), mock_objects
