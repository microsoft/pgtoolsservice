# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.admin.contracts import (GET_DATABASE_INFO_REQUEST,
                                               GetDatabaseInfoParameters,
                                               GetDatabaseInfoResponse)
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.driver.types.mysql_driver import MySQLConnection
from ossdbtoolsservice.utils import constants
from tests.integration import get_connection_details, integration_test
from tests.mocks.service_provider_mock import ServiceProviderMock
from tests.mysqlsmo_tests.utils import MockMySQLServerConnection
from tests.utils import MockMySQLCursor, MockRequestContext


class TestAdminService(unittest.TestCase):
    """Methods for testing the admin service"""

    def setUp(self):
        self.admin_service = AdminService()
        self.connection_service = ConnectionService()
        self.service_provider = ServiceProviderMock({
            constants.ADMIN_SERVICE_NAME: self.admin_service,
            constants.CONNECTION_SERVICE_NAME: self.connection_service})
        self.admin_service.register(self.service_provider)

    def test_initialization(self):
        """Test that the admin service registers its handlers correctly"""
        # Verify that the correct request handler was set up via the call to register during test setup
        self.service_provider.server.set_request_handler.assert_called_once_with(
            GET_DATABASE_INFO_REQUEST, self.admin_service._handle_get_database_info_request)

    def test_handle_get_database_info_request(self):
        """Test that the database info handler responds with the correct database info"""
        uri = 'test_uri'
        db_name = 'test_db'
        owner_name = 'test_user'
        db_size = 1024
        # Set up the request parameters
        params = GetDatabaseInfoParameters()
        params.owner_uri = uri
        request_context = MockRequestContext()

        # Set up a mock connection for the test
        mock_connection = MockMySQLServerConnection(name=db_name)
        mock_connection.get_database_owner = mock.Mock(return_value=owner_name)
        mock_connection.get_database_size = mock.Mock(return_value=db_size)
        self.connection_service.get_connection = mock.Mock(return_value=mock_connection)

        # If I send a get_database_info request
        self.admin_service._handle_get_database_info_request(request_context, params)

        # Then the service responded with the expected information
        response = request_context.last_response_params
        self.assertIsInstance(response, GetDatabaseInfoResponse)
        expected_info = {'dbname': db_name, 'owner': owner_name, 'size': db_size}
        self.assertEqual(response.database_info.options, expected_info)

        mock_connection.get_database_owner.assert_called_once()
        mock_connection.get_database_size.assert_called_once_with(db_name)

    @integration_test
    def test_get_database_info_request_integration(self):
        # Set up the request parameters
        params = GetDatabaseInfoParameters()
        params.owner_uri = 'test_uri'
        request_context = MockRequestContext()

        # Set up the connection service to return our connection
        connection = MySQLConnection(get_connection_details())
        self.connection_service.get_connection = mock.Mock(return_value=connection)

        # If I send a get_database_info request
        self.admin_service._handle_get_database_info_request(request_context, params)

        # Then the service responded with a valid database owner
        owner = request_context.last_response_params.database_info.options['owner']

        cursor = connection.cursor()
        cursor.execute('select user from mysql.user')
        usernames = [row[0] for row in cursor.fetchall()]
        self.assertIn(owner, usernames)
        connection.close()
