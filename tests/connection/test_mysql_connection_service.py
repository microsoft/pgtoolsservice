# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService with a MySQL connection"""

import unittest
from unittest import mock

import tests.utils as utils
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.connection.contracts import (ConnectionType,
                                                    ConnectRequestParams)
from ossdbtoolsservice.utils.constants import (DEFAULT_PORT,
                                               MYSQL_PROVIDER_NAME,
                                               WORKSPACE_SERVICE_NAME)
from ossdbtoolsservice.workspace import WorkspaceService
from tests.utils import MockMySQLCursor, MockMySQLConnection


class TestMySQLConnectionService(unittest.TestCase):
    """Methods for testing the connection service with a MySQL Connection"""

    def setUp(self):
        """Set up the tests with a connection service"""
        self.connection_service = ConnectionService()
        self.connection_service._service_provider = utils.get_mock_service_provider({WORKSPACE_SERVICE_NAME: WorkspaceService()},
                                                                                    provider_name=MYSQL_PROVIDER_NAME)
        # MySQLConnection runs a version query on connect
        mock_cursor = MockMySQLCursor([['5.7.29-log']])
        # Set up the mock connection for mysql's connect method to return
        self.mock_mysql_connection = MockMySQLConnection(parameters={
            'host': 'myserver',
            'dbname': 'postgres',
            'user': 'postgres'}, cursor=mock_cursor)

    def test_connect(self):
        """Test that the service connects to a MySQL server"""
        # Set up the parameters for the connection
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'user': 'mysql',
                    'password': 'password',
                    'host': 'myserver',
                    'dbname': 'mysql'
                }
            }
        })

        # Set up the connection service and call its connect method with the supported options
        with mock.patch('mysql.connector.connect', new=mock.Mock(return_value=self.mock_mysql_connection)):
            response = self.connection_service.connect(params)

        # Verify that mysql's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(self.connection_service.owner_to_connection_map[params.owner_uri].get_connection(params.type)._conn,
                      self.mock_mysql_connection)
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertFalse(response.server_info.is_cloud)

    def test_connect_with_access_token(self):
        """Test that the service connects to a MySQL server using an access token as a password"""
        # Set up the parameters for the connection
        params: ConnectRequestParams = ConnectRequestParams.from_dict({
            'ownerUri': 'someUri',
            'type': ConnectionType.DEFAULT,
            'connection': {
                'options': {
                    'user': 'mysql',
                    'azureAccountToken': 'exampleToken',
                    'host': 'myserver',
                    'dbname': 'mysql'
                }
            }
        })

        # Set up mysql instance for connection service to call
        mock_connect_method = mock.Mock(return_value=self.mock_mysql_connection)

        # Set up the connection service and call its connect method with the supported options
        with mock.patch('mysql.connector.connect', new=mock_connect_method):
            response = self.connection_service.connect(params)

        # Verify that mysql's connection method was called with password set to account token.
        mock_connect_method.assert_called_once_with(
            auth_plugin='mysql_clear_password',
            ssl_disabled=False,
            user='mysql', 
            password='exampleToken',
            host='myserver',
            port=DEFAULT_PORT[MYSQL_PROVIDER_NAME],
            database='mysql',
            ssl_verify_cert=False,
            ssl_verify_identity=False,
            )

        # Verify that mysql's connection method was called and that the
        # response has a connection id, indicating success.
        self.assertIs(self.connection_service.owner_to_connection_map[params.owner_uri].get_connection(params.type)._conn,
                      self.mock_mysql_connection)
        self.assertIsNotNone(response.connection_id)
        self.assertIsNotNone(response.server_info.server_version)
        self.assertFalse(response.server_info.is_cloud)
