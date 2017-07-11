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
            node_collection[1.2]

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
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
        generator, mock_objects = _get_mock_generator()
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
        node_collection[123]     # Force the collection to load

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


class MockNodeObject(node.NodeObject):
    @classmethod
    def _from_node_query(cls, conn: ServerConnection, **kwargs):
        pass

    def __init__(self, conn: ServerConnection, name: str):
        super(MockNodeObject, self).__init__(conn, name)


def _get_mock_generator():
    conn = ServerConnection(utils.MockConnection(None))

    mock_object1 = MockNodeObject(conn, 'a')
    mock_object1._oid = 123

    mock_object2 = MockNodeObject(conn, 'b')
    mock_object2._oid = 456

    mock_objects = [mock_object1, mock_object2]
    return mock.MagicMock(return_value=mock_objects), mock_objects
