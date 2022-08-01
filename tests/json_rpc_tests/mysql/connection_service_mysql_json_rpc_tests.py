# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME

from tests.integration import get_connection_details, integration_test
from tests.json_rpc_tests import DefaultRPCTestMessages, JSONRPCTestCase


class ConnectionServiceMySqlJSONRPCTests(unittest.TestCase):
    
    @integration_test(provider=MYSQL_PROVIDER_NAME)
    def test_connection_successful(self):
        # If I set up a connection request with valid connection parameters
        owner_uri = 'test_uri|MySQL'
        connection_details = get_connection_details()
        connection_request, language_flavor_notification = DefaultRPCTestMessages.connection_request(owner_uri, connection_details, MYSQL_PROVIDER_NAME)

        # Then when the connection request is made, a successful response notification will be returned
        def verify_connection_complete(notification):
            params = notification['params']
            print("params are : " + str(params))
            self.assertIn('connectionSummary', params)
            connection_summary = params['connectionSummary']
            self.assertEqual(connection_summary['databaseName'], connection_details['database'])
            self.assertEqual(connection_summary['serverName'], connection_details['host'])
            self.assertEqual(connection_summary['userName'], connection_details['user'])
            self.assertIsNone(params['errorMessage'])
            self.assertIn('serverInfo', params)

        connection_request.notification_verifiers[0] = (connection_request.notification_verifiers[0][0], verify_connection_complete)
        language_flavor_notification.notification_verifiers = None

        # Run the test with the valid connection request and response verifier
        test_case = JSONRPCTestCase([connection_request, language_flavor_notification])
        test_case.run(constants.MYSQL_PROVIDER_NAME)

    @integration_test(provider=MYSQL_PROVIDER_NAME)
    def test_connection_fails(self):
        # If I set up a connection request with incorrect connection parameters
        owner_uri = 'test_uri|MySQL'
        connection_details = get_connection_details()
        connection_details['database'] += 'fail'
        connection_request, language_flavor_notification = DefaultRPCTestMessages.connection_request(owner_uri, connection_details, MYSQL_PROVIDER_NAME)

        # Then when the connection request is made, a connection failed response notification will be returned
        def verify_connection_complete(notification):
            params = notification['params']
            self.assertIsNone(params['connectionSummary'])
            self.assertIsNotNone(params['errorMessage'])
            self.assertIsNotNone(params['messages'])
            self.assertIsNone(params['serverInfo'])

        connection_request.notification_verifiers[0] = (connection_request.notification_verifiers[0][0], verify_connection_complete)
        language_flavor_notification.notification_verifiers = None

        # Run the test with the incorrect connection parameters and failure response verifier
        test_case = JSONRPCTestCase([connection_request, language_flavor_notification])
        test_case.run(constants.MYSQL_PROVIDER_NAME)
