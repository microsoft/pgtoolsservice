# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import unittest
import unittest.mock as mock
from urllib.parse import urlparse

import ossdbtoolsservice.object_explorer.session as session
from ossdbtoolsservice.hosting import ServiceProvider
from ossdbtoolsservice.object_explorer.routing.pg_routing import PG_ROUTING_TABLE
from ossdbtoolsservice.connection.contracts import ConnectionDetails
from ossdbtoolsservice.object_explorer.contracts import NodeInfo
from ossdbtoolsservice.object_explorer.object_explorer_service import ObjectExplorerService, ObjectExplorerSession
from ossdbtoolsservice.utils.constants import PG_PROVIDER_NAME

class TestObjectExplorerRouting(unittest.TestCase):
    # FOLDER TESTING #######################################################
    def test_folder_init(self):
        # If: I create a folder
        label = 'FolderName'
        path = 'folder_path'
        folder = session.Folder(label, path)

        # Then: The internal state of the folder should be set up properly
        self.assertEqual(folder.path, path + '/')
        self.assertEqual(folder.label, label)

    def test_folder_as_node(self):
        # If: I have a folder and ask for it to be turned into a node
        label = 'FolderName'
        path = 'folder_path'
        current_path = '/'
        node = session.Folder(label, path).as_node(current_path)

        # Then: The node state should be setup properly
        self.assertIsInstance(node, NodeInfo)
        self.assertFalse(node.is_leaf)
        self.assertEqual(node.label, label)
        self.assertIsNotNone(urlparse(node.node_path))
        self.assertTrue(node.node_path.endswith('/'))
        self.assertEqual(node.node_type, 'Folder')

    # ROUTING TARGET TESTS #################################################
    def test_routing_target_init_no_folders(self):
        # If: I create a routing target without any folders defined
        node_generator = mock.MagicMock()
        rt = session.RoutingTarget(None, node_generator)

        # Then: The internal state should show an empty array of folders
        self.assertListEqual(rt.folders, [])
        self.assertIs(rt.node_generator, node_generator)

    def test_routing_target_init_with_folders(self):
        # If: I create a routing target with folders defined
        node_generator = mock.MagicMock()
        folder_list = [session.Folder('FolderName', 'folder_path')]
        rt = session.RoutingTarget(folder_list, node_generator)

        # Then: The internal state should reflect a list of folders being provided
        self.assertIs(rt.folders, folder_list)
        self.assertIs(rt.node_generator, node_generator)

    def test_routing_target_get_nodes_empty(self):
        # If: I ask for nodes for an empty routing target
        rt = session.RoutingTarget(None, None)
        output = rt.get_nodes(False, '/', ObjectExplorerSession('session_id', ConnectionDetails()), {})

        # Then: The results should be empty
        self.assertListEqual(output, [])

    def test_routing_target_get_nodes_not_empty(self):
        # Setup: Create mock node generator and folder node list
        node1 = NodeInfo()
        node2 = NodeInfo()
        node_generator = mock.MagicMock(return_value=[node1, node2])
        folder_list = [session.Folder('Folder1', 'fp1'), session.Folder('Folder2', 'fp2')]

        # If: I ask for nodes for a routing target
        rt = session.RoutingTarget(folder_list, node_generator)
        current_path = '/'
        match_params = {}
        object_explorer_session = ObjectExplorerSession('session_id', ConnectionDetails())
        output = rt.get_nodes(False, current_path, session, match_params)

        # Then:
        # ... I should get back a list of nodes
        self.assertIsInstance(output, list)
        for node in output:
            self.assertIsInstance(node, NodeInfo)
        self.assertEqual(len(output), 4)
        self.assertEqual(output[0].node_type, 'Folder')
        self.assertEqual(output[1].node_type, 'Folder')
        self.assertIs(output[2], node1)
        self.assertIs(output[3], node2)

        # ... The node generator should have been called
        node_generator.assert_called_once_with(False, current_path, object_explorer_session, match_params)

    # ROUTING TABLE TESTS ##################################################
    def test_routing_table(self):
        # Make sure that all keys in the routing table are regular expressions
        # Make sure that all items in the routing table are RoutingTargets
        re_class = re.compile('^/$').__class__
        for key, item in PG_ROUTING_TABLE.items():
            self.assertIsInstance(key, re_class)
            self.assertIsInstance(item, session.RoutingTarget)

    def test_routing_invalid_path(self):
        # If: Ask to route a path without a route
        # Then: I should get an exception
        service_provider =  ServiceProvider(None, {}, PG_PROVIDER_NAME)
        object_explorer_service = ObjectExplorerService()
        object_explorer_service.service_provider = service_provider
        object_explorer_service._routing_table = PG_ROUTING_TABLE

        with self.assertRaises(ValueError):
            object_explorer_service._route_request(False, 
                ObjectExplorerSession('session_id', ConnectionDetails()), '!/invalid!/')

    def test_routing_match(self):
        # If: Ask to route a request that is valid
        service_provider =  ServiceProvider(None, {}, PG_PROVIDER_NAME)
        object_explorer_service = ObjectExplorerService()
        object_explorer_service.service_provider = service_provider
        object_explorer_service._routing_table = PG_ROUTING_TABLE
        output = object_explorer_service._route_request(False, ObjectExplorerSession('session_id', ConnectionDetails()), '/')

        # Then: The output should be a list of nodes
        self.assertIsInstance(output, list)
        for node in output:
            self.assertIsInstance(node, NodeInfo)
