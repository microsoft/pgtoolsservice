# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsqltoolsservice.admin import AdminService
from pgsqltoolsservice.admin.contracts import GET_DATABASE_INFO_REQUEST, GetDatabaseInfoParameters, GetDatabaseInfoResponse
from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.utils import constants
from tests.mocks.service_provider_mock import ServiceProviderMock
from tests.utils import MockConnection, MockCursor, MockRequestContext


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
        user_name = 'test_user'
        # Set up the request parameters
        params = GetDatabaseInfoParameters()
        params.owner_uri = uri
        request_context = MockRequestContext()

        # Set up a mock connection and cursor for the test
        mock_query_results = [(user_name,)]
        mock_cursor = MockCursor(mock_query_results)
        mock_connection = MockConnection({'dbname': db_name}, mock_cursor)
        self.connection_service.get_connection = mock.Mock(return_value=mock_connection)

        # If I send a get_database_info request
        self.admin_service._handle_get_database_info_request(request_context, params)

        # Then the service responded with the expected information
        response = request_context.last_response_params
        self.assertIsInstance(response, GetDatabaseInfoResponse)
        expected_info = {'owner': user_name}
        self.assertEqual(response.database_info.options, expected_info)

        # And the service retrieved the owner name using a query with the database name as a parameter
        mock_cursor.execute.assert_called_once_with(mock.ANY, (db_name,))