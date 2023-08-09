# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from textwrap import (dedent)
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.connection.contracts import ConnectionType
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.metadata.contracts import (METADATA_LIST_REQUEST,
                                                  MetadataListParameters,
                                                  MetadataListResponse,
                                                  MetadataSchemaParameters,
                                                  MetadataSchemaResponse,
                                                  MetadataType, ObjectMetadata)
from ossdbtoolsservice.utils import constants
from tests.mocks.service_provider_mock import ServiceProviderMock
from tests.pgsmo_tests.utils import MockPGServerConnection, MockPsycopgConnection
from tests.utils import (
    MockCursor, MockRequestContext, MockThread)
from tests.integration import get_connection_details, integration_test
from ossdbtoolsservice.driver.types.psycopg_driver import (PostgreSQLConnection)


class TestMetadataService(unittest.TestCase):
    """Methods for testing the metadata service"""

    def setUp(self):
        self.metadata_service = MetadataService()
        self.connection_service = ConnectionService()
        self.service_provider = ServiceProviderMock({
            constants.METADATA_SERVICE_NAME: self.metadata_service,
            constants.CONNECTION_SERVICE_NAME: self.connection_service})
        self.metadata_service.register(self.service_provider)
        self.test_uri = 'test_uri'

    def test_initialization(self):
        """Test that the metadata service registers its handlers correctly"""

        # Verify that request handlers were set up via the call to register during test setup
        self.service_provider.server.set_request_handler.assert_called()

    def test_metadata_list_request(self):
        """Test that the metadata list handler properly starts a thread to list metadata and responds with the list"""
        # Set up the parameters and mocks for the request
        expected_metadata = [
            ObjectMetadata(schema='schema1', name='table1', metadata_type=MetadataType.TABLE),
            ObjectMetadata(schema='schema1', name='view1', metadata_type=MetadataType.VIEW),
            ObjectMetadata(schema='schema1', name='function1', metadata_type=MetadataType.FUNCTION),
            ObjectMetadata(schema='schema1', name='table2', metadata_type=MetadataType.TABLE),
            ObjectMetadata(schema='schema2', name='view1', metadata_type=MetadataType.VIEW),
            ObjectMetadata(schema='schema2', name='function1', metadata_type=MetadataType.FUNCTION),
        ]

        metadata_type_to_str_map = {
            MetadataType.TABLE: 't',
            MetadataType.VIEW: 'v',
            MetadataType.FUNCTION: 'f'
        }

        # Query results have schema_name, object_name, and object_type columns in that order
        list_query_result = [(metadata.schema, metadata.name, metadata_type_to_str_map[metadata.metadata_type]) for metadata in expected_metadata]
        mock_cursor = MockCursor(list_query_result)
        mock_psycopg_connection = MockPsycopgConnection(cursor=mock_cursor, dsn_parameters='host=test dbname=test')
        mock_connection = MockPGServerConnection(cur=mock_cursor, connection=mock_psycopg_connection)
        mock_cursor.connection = mock_psycopg_connection
        self.connection_service.get_connection = mock.Mock(return_value=mock_connection)
        request_context = MockRequestContext()
        params = MetadataListParameters()
        params.owner_uri = self.test_uri
        mock_thread = MockThread()
        with mock.patch('threading.Thread', new=mock.Mock(side_effect=mock_thread.initialize_target)):
            # If I call the metadata list request handler
            self.metadata_service._handle_metadata_list_request(request_context, params)
            # Then the worker thread was kicked off
            self.assertEqual(mock_thread.target, self.metadata_service._metadata_list_worker)
            mock_thread.start.assert_called_once()
        # And the worker retrieved the correct connection and executed a query on it
        self.connection_service.get_connection.assert_called_once_with(self.test_uri, ConnectionType.DEFAULT)
        mock_cursor.execute.assert_called_once()
        # And the handler responded with the expected results
        self.assertIsNone(request_context.last_error_message)
        self.assertIsNone(request_context.last_notification_method)
        response = request_context.last_response_params
        self.assertIsInstance(response, MetadataListResponse)
        for index, actual_metadata in enumerate(response.metadata):
            self.assertIsInstance(actual_metadata, ObjectMetadata)
            self.assertEqual(actual_metadata.schema, expected_metadata[index].schema)
            self.assertEqual(actual_metadata.name, expected_metadata[index].name)
            self.assertEqual(actual_metadata.metadata_type, expected_metadata[index].metadata_type)

    def test_metadata_list_request_error(self):
        """Test that the proper error response is sent if there is an error while handling a metadata list request"""
        request_context = MockRequestContext()
        params = MetadataListParameters()
        params.owner_uri = self.test_uri
        self.metadata_service._list_metadata = mock.Mock(side_effect=Exception)
        mock_thread = MockThread()
        with mock.patch('threading.Thread', new=mock.Mock(side_effect=mock_thread.initialize_target)):
            # If I call the metadata list request handler and its execution raises an error
            self.metadata_service._handle_metadata_list_request(request_context, params)
        # Then an error response is sent
        self.assertIsNotNone(request_context.last_error_message)
        self.assertIsNone(request_context.last_notification_method)
        self.assertIsNone(request_context.last_response_params)

    @integration_test
    def test_metadata_schema_requests(self):
        connection = PostgreSQLConnection(get_connection_details())
        self.connection_service.get_connection = mock.Mock(return_value=connection)

        cur = connection.cursor()
        cur.execute("""
            CREATE TABLE students (
                studentid SERIAL PRIMARY KEY,
                firstname VARCHAR(100) NOT NULL,
                lastname VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                birthdate DATE NOT NULL,
                enrollmentyear INT CHECK
                    (enrollmentyear >= 2000 AND enrollmentyear <= EXTRACT(YEAR FROM CURRENT_DATE))
            );
            """)

        request_context = MockRequestContext()
        params = MetadataSchemaParameters()
        params.owner_uri = self.test_uri

        mock_thread = MockThread()
        with mock.patch('threading.Thread', new=mock.Mock(side_effect=mock_thread.initialize_target)):
            self.metadata_service._handle_metadata_schema_request(request_context, params)

        response = request_context.last_response_params
        self.assertIsInstance(response, MetadataSchemaResponse)

        tab = "\t"
        self.maxDiff = None # show the whole diff
        self.assertEqual(response.description, dedent(f"""\
            ## PostgreSQL database schema

            ## Tables and columns in the schema, in the form:
            table_name
            {tab}column_name/type
            {tab}column_name/type

            students
            {tab}studentid/int
            {tab}firstname/varchar
            {tab}lastname/varchar
            {tab}email/varchar
            {tab}birthdate/date
            {tab}enrollmentyear/int

            ## Table constraints, in the form:
            table_name
            {tab}constraint_def
            {tab}constraint_def

            students
            {tab}primary key (studentid)
            {tab}unique (email)

            ## Table indexes, in the form:
            table_name
            {tab}type (column_name, column_name)
            {tab}type (column_name, column_name)

            students
            {tab}btree (email)
            {tab}btree (studentid)
            """))
