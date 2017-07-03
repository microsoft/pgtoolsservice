# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import pgsmo.objects.node_object as no


class TestNodeCollection(unittest.TestCase):
    def test_init(self):
        # Setup: Create a mock generator
        generator = mock.MagicMock()

        # If: I initialize a node collection
        nc = no.NodeCollection(generator)

        # Then: The internal properties should be set properly
        self.assertIs(nc._generator, generator)
        self.assertIsNone(nc._items)

    def test_index_bad_type(self):
        # Setup: Create a mock generator and node collection
        generator = mock.MagicMock()
        nc = no.NodeCollection(generator)

        # If: I ask for items with an invalid type for the index
        # Then: I should get an exception
        with self.assertRaises(TypeError):
            nc[1.2]

    def test_index_no_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)

        # If: I get an item that doesn't have a matching oid
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            nc[789]

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(nc._items, mock_objects)

    def test_index_no_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)

        # If: I get an item that doesn't have a matching name
        # Then:
        # ... I should get an exception
        with self.assertRaises(NameError):
            nc['c']

        # ... The generator should have been called, tho
        generator.assert_called_once()
        self.assertIs(nc._items, mock_objects)

    def test_index_match_oid(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)

        # If: I get an item that has a matching oid
        o = nc[456]

        # Then: The item I have should be the expected item
        self.assertIs(o, mock_objects[1])

    def test_index_match_name(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)

        # If: I get an item that has a matching oid
        o = nc['b']

        # Then: The item I have should be the expected item
        self.assertIs(o, mock_objects[1])

    def test_iterator(self):
        # Setup: Create a mock generator and node collection
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)

        # If: I iterate over the items in the collection
        o = [n for n in nc]

        # Then: The list should be equivalent to the list of objects
        self.assertListEqual(o, mock_objects)

    def test_reset(self):
        # Setup: Create a mock generator and node collection that has been loaded
        generator, mock_objects = _get_mock_generator()
        nc = no.NodeCollection(generator)
        nc[123]     # Force the collection to load

        # If: I reset the collection
        nc.reset()

        # Then:
        # ... The item collection should be none
        self.assertIsNone(nc._items)


class TestNodeObject(unittest.TestCase):
    def test_init(self):
        # If: I create a node object
        conn = {}
        node_obj = no.NodeObject(conn, 'abc')

        # Then: The properties should be assigned as defined
        self.assertIsNone(node_obj._oid)
        self.assertIsNone(node_obj.oid)

        self.assertEqual(node_obj._name, 'abc')
        self.assertEqual(node_obj.name, 'abc')

        self.assertIs(node_obj._conn, conn)

    def test_get_nodes(self):
        # Setup:
        # ... Create a mockup of a connection wrapper
        version = (1, 1, 1)
        class MockConn:
            def __init__(self):
                self.version = version
        mock_conn = MockConn()

        # ... Create a mock template renderer
        mock_render = mock.MagicMock(return_value="SQL")
        mock_template_path = mock.MagicMock(return_value="path")

        # ... Create a mock query executor
        mock_objs = [{'name': 'abc', 'oid': 123}, {'name': 'def', 'oid': 456}]
        mock_executor = mock.MagicMock(return_value=([{}, {}], mock_objs))

        # ... Create a mock generator
        mock_output = {}
        mock_generator = mock.MagicMock(return_value=mock_output)

        # ... Do the patching
        with mock.patch('pgsmo.objects.node_object.t.render_template', mock_render, create=True):
            with mock.patch('pgsmo.objects.node_object.t.get_template_path', mock_template_path, create=True):
                with mock.patch('pgsmo.objects.node_object.q.execute_dict', mock_executor, create=True):
                    # If: I ask for a collection of nodes
                    kwargs = {'arg1': 'something'}
                    nodes = no.get_nodes(mock_conn, 'root', mock_generator, **kwargs)

        # Then:
        # ... The template path should have been called once
        mock_template_path.assert_called_once_with('root', 'nodes.sql', version)

        # ... The template renderer should have been called once
        mock_render.assert_called_once_with('path', **kwargs)

        # ... A query should have been executed
        mock_executor.assert_called_once_with(mock_conn, 'SQL')

        # ... The generator should have been called twice with different object props
        mock_generator.assert_any_call(mock_conn, **mock_objs[0])
        mock_generator.assert_any_call(mock_conn, **mock_objs[1])

        # ... The output list of nodes should match what the generator created
        self.assertIsInstance(nodes, list)
        self.assertListEqual(nodes, [mock_output, mock_output])


def _get_mock_generator():
    mock_object1 = no.NodeObject(None, 'a')
    mock_object1._oid = 123

    mock_object2 = no.NodeObject(None, 'b')
    mock_object2._oid = 456

    mock_objects = [mock_object1, mock_object2]
    return mock.MagicMock(return_value=mock_objects), mock_objects

