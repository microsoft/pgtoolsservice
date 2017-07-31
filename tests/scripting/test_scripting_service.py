# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from typing import List, Dict  # noqa

from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.connection.contracts.common import ConnectionType
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
import tests.utils as utils
from pgsqltoolsservice.scripting import ScriptingService
from pgsqltoolsservice.scripting.contracts.scriptas_request import ScriptOperation, ScriptAsParameters
import pgsmo.utils.templating as Template
import pgsmo.utils.querying as querying
from pgsmo.objects.table.table import Table
from pgsmo.objects.view.view import View
from pgsmo.objects.database.database import Database
from pgsmo.objects.server.server import Server

"""Module for testing the scripting service"""


class TestScriptingService(unittest.TestCase):
    """Methods for testing the scripting service"""

    def setUp(self):
        """Set up mock objects for testing the scripting service.
        Ran before each unit test.
        """
        self.cursor = utils.MockCursor(None)
        self.connection = utils.MockConnection(cursor=self.cursor)
        self.cursor.connection = self.connection
        self.connection_service = ConnectionService()
        self.service_provider = ServiceProvider(None, {})
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service}
        self.service_provider._is_initialized = True
        self.request_context = utils.MockRequestContext()

        self.cursor_cancel = utils.MockCursor(None)
        self.connection_cancel = utils.MockConnection(cursor=self.cursor_cancel)
        self.cursor_cancel.connection = self.connection_cancel

        def connection_side_effect(owner_uri: str, connection_type: ConnectionType):
            if connection_type is ConnectionType.QUERY_CANCEL:
                return self.connection_cancel
            else:
                return self.connection

        self.connection_service.get_connection = mock.Mock(side_effect=connection_side_effect)
        self.table_metadata = {"metadataTypeName": "Table"}
        self.view_metadata = {"metadataTypeName": "View"}
        self.database_metadata = {"metadataTypeName": "Database"}
        self.utils = querying.ConnectionUtils()
        self.success = False

    def test_initialization(self):
        # Setup: Create a scripting service with a mocked out service
        # provider
        mock_server_set_request = mock.MagicMock()
        mock_server = JSONRPCServer(None, None)
        mock_server.set_request_handler = mock_server_set_request
        mock_service_provider = ServiceProvider(mock_server, {}, None)
        service = ScriptingService()

        # If: I initialize the service
        service.register(mock_service_provider)

        # Then:
        # ... There should have been request handlers set
        mock_server_set_request.assert_called()

        # ... Each mock call should have an IncomingMessageConfig and a function pointer
        for mock_call in mock_server_set_request.mock_calls:
            self.assertIsInstance(
                mock_call[1][0], IncomingMessageConfiguration)
            self.assertTrue(callable(mock_call[1][1]))

    def test_handle_scriptas_request(self):
        """ Test _handle_scriptas_request function """
        mock_service = ScriptingService()
        metadata = {
            "schema": "public",
            "name": "foo"
        }
        params = {
            "metadata": metadata,
            "operation": ScriptOperation.Select,
            "owner_uri": "test_uri"
        }

        mock_conn_service = mock.MagicMock()
        mock_conn_service.get_connection = mock.MagicMock(return_value=self.connection)
        mock_service._service_provider = mock.MagicMock(return_value=mock_conn_service)
        mock_service._scripting_operation = mock.MagicMock(return_value=None)
        self.request_context.send_response = mock.MagicMock(side_effect=self._success())
        mock_params = ScriptAsParameters.from_dict(params)
        mock_service._handle_scriptas_request(self.request_context, mock_params)
        self.assertTrue(self.success)

    def test_script_as_select(self):
        """Test getting select script for all objects"""
        # Set up the service and the objects
        scripter = utils.MockScripter(self.connection)
        metadata = {
            "schema": "public",
            "name": "foo"
        }
        service = ScriptingService()
        service.script_as_select = mock.MagicMock(return_value=scripter.script_as_select(metadata))

        # If I try to get select script for any object
        result = service.script_as_select()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)

    def test_script_as_create(self):
        """Test getting create script for all objects"""
        # Set up the service and the objects
        scripter = utils.MockScripter(self.connection)
        service = ScriptingService()

        # Table
        self._test_table_create_script(scripter, service)

        # View
        self._test_view_create_script(scripter, service)

        # Database
        self._test_database_create_script(scripter, service)

    # PRIVATE HELPER FUNCTIONS ####################################################

    def assertNotNoneOrEmpty(self, result: str) -> bool:
        """Assertion to confirm a string to be not none or empty"""
        self.assertIsNotNone(result) and self.assertTrue(len(result))

    def _success(self):
        self.success = True

    def _test_table_create_script(self, service, scripter):
        """ Helper function to test create script for tables """
        # Set up the mocks
        mock_table = Table(None, None, 'test')

        def table_mock_fn(connection, operation: str):
            mock_table._template_root = mock.MagicMock(return_value=Table.TEMPLATE_ROOT)
            mock_table._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            connection_version = self.utils.get_server_version(connection)
            mock_template = Template.get_template_path(mock_table._template_root(), f"{operation}.sql", connection_version)
            result = Template.render_template(mock_template, **mock_table._create_query_data())
            return result

        def scripter_mock_fn():
            mock_table.script = mock.MagicMock(return_value=table_mock_fn(self.connection, "create"))
            return mock_table.script()

        scripter.get_table_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_table_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertIsNotNone(result)

    def _test_view_create_script(self, service, scripter):
        """ Helper function to test create script for views """
        # Set up the mocks
        mock_view = View(None, None, 'test')

        def view_mock_fn(connection, operation: str):
            mock_view._template_root = mock.MagicMock(return_value=View.TEMPLATE_ROOT)
            mock_view._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            connection_version = self.utils.get_server_version(connection)
            mock_template = Template.get_template_path(mock_view._template_root(), f"{operation}.sql", connection_version)
            result = Template.render_template(mock_template, **mock_view._create_query_data())
            return result

        def scripter_mock_fn():
            mock_view.script = mock.MagicMock(return_value=view_mock_fn(self.connection, "create"))
            return mock_view.script()

        scripter.get_view_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_view_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertIsNotNone(result)

    def _test_database_create_script(self, service, scripter):
        """ Helper function to test create script for views """
        # Set up the mocks
        mock_connection = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        mock_server = Server(mock_connection)
        mock_database = Database(mock_server, 'test')

        def database_mock_fn(connection, operation: str):
            mock_database._template_root = mock.MagicMock(return_value=Database.TEMPLATE_ROOT)
            mock_database._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            connection_version = self.utils.get_server_version(connection)
            mock_template = Template.get_template_path(mock_database._template_root(), f"{operation}.sql", connection_version)
            result = Template.render_template(mock_template, **mock_database._create_query_data())
            return result

        def scripter_mock_fn():
            mock_database.script = mock.MagicMock(return_value=database_mock_fn(self.connection, "create"))
            return mock_database.script()

        scripter.get_database_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_database_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
