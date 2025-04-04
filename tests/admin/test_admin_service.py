# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

import psycopg
from psycopg import sql

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.admin.contracts import (
    GET_DATABASE_INFO_REQUEST,
    GetDatabaseInfoParameters,
    GetDatabaseInfoResponse,
)
from ossdbtoolsservice.connection import ConnectionService, PooledConnection, ServerConnection
from ossdbtoolsservice.utils import constants
from tests.integration import get_connection_details, integration_test
from tests.mocks.service_provider_mock import ServiceProviderMock
from tests.pgsmo_tests.utils import MockPGServerConnection
from tests.utils import MockCursor, MockPsycopgConnection, MockRequestContext


class TestAdminService(unittest.TestCase):
    """Methods for testing the admin service"""

    def setUp(self) -> None:
        self.admin_service = AdminService()
        self.connection_service = ConnectionService()
        self.service_provider = ServiceProviderMock(
            {
                constants.ADMIN_SERVICE_NAME: self.admin_service,
                constants.CONNECTION_SERVICE_NAME: self.connection_service,
            }
        )
        self.admin_service.register(self.service_provider)

    def test_initialization(self) -> None:
        """Test that the admin service registers its handlers correctly"""
        # Verify that the correct request handler was set up
        # via the call to register during test setup
        self.service_provider.server.set_request_handler.assert_called_once_with(
            GET_DATABASE_INFO_REQUEST, self.admin_service._handle_get_database_info_request
        )

    def test_handle_get_database_info_request(self) -> None:
        """Test that the database info handler responds with the correct database info"""
        uri = "test_uri"
        db_name = "test_db"
        user_name = "test_user"
        # Set up the request parameters
        params = GetDatabaseInfoParameters()
        params.owner_uri = uri
        request_context = MockRequestContext()

        # Set up a mock connection and cursor for the test
        mock_query_results = [(user_name,)]
        mock_cursor = MockCursor(mock_query_results)
        mock_psycopg_connection = MockPsycopgConnection(
            cursor=mock_cursor, dsn_parameters=f"host=test dbname={db_name}"
        )
        mock_connection = MockPGServerConnection(
            cur=mock_cursor, connection=mock_psycopg_connection, name=db_name
        )
        mock_cursor.connection = mock_psycopg_connection
        pooled_connection = PooledConnection(lambda _: mock_connection, lambda _: None)
        self.connection_service.get_pooled_connection = mock.Mock(
            return_value=pooled_connection
        )

        # If I send a get_database_info request
        self.admin_service._handle_get_database_info_request(request_context, params)

        # Then the service responded with the expected information
        response = request_context.last_response_params
        self.assertIsInstance(response, GetDatabaseInfoResponse)
        expected_info = {"dbname": db_name, "owner": user_name, "size": None}
        self.assertEqual(response.database_info.options, expected_info)

        # And the service retrieved the owner name using a query
        # with the database name as a parameter
        owner_query = sql.SQL(
            "SELECT pg_catalog.pg_get_userbyid(db.datdba) "
            f"FROM pg_catalog.pg_database db WHERE db.datname = '{db_name}'"
        )
        mock_cursor.execute.assert_called_once_with(owner_query, params=None)

    @integration_test
    def test_get_database_info_request_integration(self) -> None:
        # Set up the request parameters
        params = GetDatabaseInfoParameters()
        params.owner_uri = "test_uri"
        request_context = MockRequestContext()

        # Set up the connection service to return our connection
        conn = psycopg.connect(**get_connection_details())
        connection = ServerConnection(conn)
        pooled_connection = PooledConnection(lambda _: connection, lambda _: None)
        self.connection_service.get_pooled_connection = mock.Mock(
            return_value=pooled_connection
        )

        # If I send a get_database_info request
        self.admin_service._handle_get_database_info_request(request_context, params)

        # Then the service responded with a valid database owner
        owner = request_context.last_response_params.database_info.options["owner"]

        cursor = connection.cursor()
        cursor.execute("select usename from pg_catalog.pg_user")
        usernames = [row[0] for row in cursor.fetchall()]
        self.assertIn(owner, usernames)
        connection.close()
