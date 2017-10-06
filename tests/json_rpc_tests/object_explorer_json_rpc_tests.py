# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import functools
import json
import unittest

from pgsqltoolsservice.hosting.json_message import JSONRPCMessageType
from tests.integration import create_extra_test_database, get_connection_details, integration_test
from tests.json_rpc_tests import DefaultRPCTestMessages, JSONRPCTestCase, RPCTestMessage


class ObjectExplorerJSONRPCTests(unittest.TestCase):
    @integration_test
    def test_object_explorer(self):
        # Set up a database connection for the test
        owner_uri = 'test_uri'
        connection_details = get_connection_details()
        connection_messages = DefaultRPCTestMessages.connection_request(owner_uri, connection_details)
        test_messages = [connection_messages[0], connection_messages[1]]

        # If I send a createsession request, a session will be created and provide a database at the root node
        expected_session_id = f'objectexplorer://{connection_details["user"]}@{connection_details["host"]}:{connection_details["dbname"]}/'

        def session_created_verifier(notification):
            params = notification['params']
            self.assertIsNone(params['errorMessage'])
            self.assertTrue(params['success'])
            self.assertIn('rootNode', params)
            root_node = params['rootNode']
            self.assertEqual(root_node['label'], connection_details['dbname'])
            self.assertEqual(root_node['nodeType'], 'Database')
            self.assertIn('metadata', root_node)
            metadata = root_node['metadata']
            self.assertEqual(metadata['metadataTypeName'], 'Database')
            self.assertEqual(metadata['name'], connection_details['dbname'])

        create_session_request = RPCTestMessage(
            'objectexplorer/createsession',
            '{{"options":{}}}'.format(json.dumps(connection_details)),
            JSONRPCMessageType.Request,
            response_verifier=lambda response: self.assertEqual(response['result']['sessionId'], expected_session_id),
            notification_verifiers=[(lambda notification: notification['method'] == 'objectexplorer/sessioncreated', session_created_verifier)])

        # If I expand nodes in Object Explorer, then the expected child nodes will be included in the response
        def expand_completed_verifier(node_path, expected_nodes, exact_node_match, notification):
            params = notification['params']
            self.assertIsNone(params['errorMessage'])
            self.assertEqual(params['nodePath'], node_path)
            nodes = params['nodes']
            self.assertGreater(len(nodes), 0)
            found_nodes = set()
            for node in nodes:
                self.assertIsNone(node['errorMessage'])
                found_nodes.add(node['label'])
            if exact_node_match:
                self.assertEqual(found_nodes, expected_nodes)
            else:
                for node in expected_nodes:
                    self.assertIn(node, found_nodes)

        def create_expand_test_message(node_path, expected_nodes, exact_node_match):
            return RPCTestMessage(
                'objectexplorer/expand',
                '{{"sessionId":"{}","nodePath":"{}"}}'.format(expected_session_id, node_path),
                JSONRPCMessageType.Request,
                response_verifier=lambda response: self.assertTrue(response['result']),
                notification_verifiers=[(
                    lambda notification: notification['method'] == 'objectexplorer/expandCompleted' and notification['params']['nodePath'] == node_path,
                    functools.partial(expand_completed_verifier, node_path, expected_nodes, exact_node_match))]
            )

        extra_db_name = create_extra_test_database()

        expand_server_request = create_expand_test_message(expected_session_id, {'Databases', 'Roles', 'Tablespaces', 'System Databases'}, True)
        expand_databases_request = create_expand_test_message('/databases/', {connection_details['dbname'], extra_db_name}, False)
        expand_system_databases_request = create_expand_test_message('/systemdatabases/', {'template0'}, False)
        expand_roles_request = create_expand_test_message('/roles/', {connection_details['user']}, False)
        expand_tablespaces_request = create_expand_test_message('/tablespaces/', {}, False)

        # If I send a refresh request, then the expected child nodes are included in the response
        refresh_databases_request = RPCTestMessage(
            'objectexplorer/refresh',
            '{{"sessionId":"{session_id}","nodePath":"/databases/"}}'.format(session_id=expected_session_id),
            JSONRPCMessageType.Request,
            response_verifier=lambda response: self.assertTrue(response['result']),
            notification_verifiers=[(
                lambda notification: notification['method'] == 'objectexplorer/expandCompleted' and notification['params']['nodePath'] == '/databases/',
                functools.partial(expand_completed_verifier, '/databases/', {connection_details['dbname']}, False))]
        )

        # Run the test with the connect, createsession, expand, and refresh requests
        test_messages += [create_session_request, expand_server_request, expand_databases_request, refresh_databases_request, expand_roles_request,
                          expand_tablespaces_request, expand_system_databases_request]
        JSONRPCTestCase(test_messages).run()
