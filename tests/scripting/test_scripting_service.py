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
from pgsqltoolsservice.hosting import (
    JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
)
import tests.utils as utils
from pgsqltoolsservice.scripting.scripter import Scripter
from pgsqltoolsservice.scripting.scripting_service import ScriptingService
from pgsqltoolsservice.scripting.contracts.scriptas_request import (
    ScriptOperation, ScriptAsParameters
)
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
        self.connection = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"}, cursor=self.cursor)
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

    def test_scripting_operation(self):
        """ Test _scripting_operation function """
        # Set up mock objects
        mock_service = ScriptingService()
        operations = [ScriptOperation.Create, ScriptOperation.Select,
                      ScriptOperation.Insert, ScriptOperation.Update,
                      ScriptOperation.Delete]
        objects = ["Database", "View", "Table"]

        mock_service.script_as_select = mock.MagicMock()
        mock_service.script_as_create = mock.MagicMock()
        mock_service.script_as_update = mock.MagicMock()
        mock_service.script_as_delete = mock.MagicMock()
        mock_service.script_as_insert = mock.MagicMock()

        # When called with various scripting operations and objects
        for op in operations:
            for obj in objects:
                mock_service._scripting_operation(op.value, self.connection, {"metadataTypeName": obj})

        # I should see calls being made for the different script operations
        self.assertEqual(True, mock_service.script_as_select.called)
        self.assertEqual(True, mock_service.script_as_create.called)
        self.assertEqual(True, mock_service.script_as_update.called)
        self.assertEqual(True, mock_service.script_as_insert.called)

        # If I use an invalid script operation, I should get back an exception
        for obj in objects:
            with self.assertRaises(Exception):
                self.assertRaises(mock_service._scripting_operation("bogus value", self.connection, {"metadataTypeName": obj}))

    def test_script_as_select(self):
        """Test getting select script for all objects"""
        # Set up the service and the objects
        mock_connection = utils.MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        scripter = Scripter(mock_connection)
        service = ScriptingService()
        metadata = {
            "schema": "public",
            "name": "foo"
        }
        service.script_as_select = mock.MagicMock(return_value=scripter.script_as_select(metadata))

        # If I try to get select script for any object
        result = service.script_as_select()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)

    def test_script_as_create(self):
        """Test getting create script for all objects"""
        # Set up the service and the objects
        mock_scripter = Scripter(self.connection)
        service = ScriptingService()

        # Table
        self._test_table_create_script(mock_scripter, service)

        # View
        self._test_view_create_script(mock_scripter, service)

        # Database
        self._test_database_create_script(mock_scripter, service)

    def test_script_as_delete(self):
        """ Test getting delete script for all objects """
        mock_scripter = Scripter(self.connection)
        service = ScriptingService()

        # Table
        self._test_table_delete_script(mock_scripter, service)

        # View
        self._test_view_delete_script(mock_scripter, service)

        # Database
        self._test_database_delete_script(mock_scripter, service)

    # PRIVATE HELPER FUNCTIONS ####################################################

    # CREATE SCRIPTS ##############################################################

    def assertNotNoneOrEmpty(self, result: str) -> bool:
        """Assertion to confirm a string to be not none or empty"""
        self.assertIsNotNone(result) and self.assertTrue(len(result))

    def _success(self):
        self.success = True

    def _test_table_create_script(self, scripter, service):
        """ Helper function to test create script for tables """
        # Set up the mocks
        mock_table = Table(None, None, 'test')

        def table_mock_fn(connection):
            mock_table._template_root = mock.MagicMock(return_value=Table.TEMPLATE_ROOT)
            mock_table._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_table.create_script(connection)
            return result

        def scripter_mock_fn():
            mock_table.create_script = mock.MagicMock(return_value=table_mock_fn(self.connection))
            return mock_table.create_script()

        scripter.get_table_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_table_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)

    def _test_view_create_script(self, scripter, service):
        """ Helper function to test create script for views """
        # Set up the mocks
        mock_view = View(None, None, 'test')

        def view_mock_fn(connection):
            mock_view._template_root = mock.MagicMock(return_value=View.TEMPLATE_ROOT)
            mock_view._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_view.create_script(connection)
            return result

        def scripter_mock_fn():
            mock_view.create_script = mock.MagicMock(return_value=view_mock_fn(self.connection))
            return mock_view.create_script()

        scripter.get_view_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_view_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertIsNotNone(result)

    def _test_database_create_script(self, scripter, service):
        """ Helper function to test create script for views """
        # Set up the mocks
        mock_server = Server(self.connection)
        mock_database = Database(mock_server, 'test')

        def database_mock_fn(connection):
            mock_database._template_root = mock.MagicMock(return_value=Database.TEMPLATE_ROOT)
            mock_database._create_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_database.create_script(connection)
            return result

        def scripter_mock_fn():
            mock_database.create_script = mock.MagicMock(return_value=database_mock_fn(self.connection))
            return mock_database.create_script()

        scripter.get_database_create_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_create = mock.MagicMock(return_value=scripter.get_database_create_script())

        # If I try to get select script for any object
        result = service.script_as_create()

        # The result shouldn't be none or an empty string
        self.assertIsNotNone(result)

    # DELETE SCRIPTS ##############################################################

    def _test_table_delete_script(self, scripter, service):
        """ Helper function to test delete script for tables """
        # Set up the mocks
        mock_table = Table(None, None, 'test')

        def table_mock_fn(connection):
            mock_table._template_root = mock.MagicMock(return_value=Table.TEMPLATE_ROOT)
            mock_table._delete_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_table.delete_script(connection)
            return result

        def scripter_mock_fn():
            mock_table.delete_script = mock.MagicMock(return_value=table_mock_fn(self.connection))
            return mock_table.delete_script()

        scripter.get_table_delete_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_delete = mock.MagicMock(return_value=scripter.get_table_delete_script())

        # If I try to get select script for any object
        result = service.script_as_delete()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)

    def _test_view_delete_script(self, scripter, service):
        """ Helper function to test delete script for views """
        # Set up the mocks
        mock_view = View(None, None, 'test')

        def view_mock_fn(connection):
            mock_view._template_root = mock.MagicMock(return_value=View.TEMPLATE_ROOT)
            mock_view._delete_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_view.delete_script(connection)
            return result

        def scripter_mock_fn():
            mock_view.delete_script = mock.MagicMock(return_value=view_mock_fn(self.connection))
            return mock_view.delete_script()

        scripter.get_view_delete_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_delete = mock.MagicMock(return_value=scripter.get_view_delete_script())

        # If I try to get select script for any object
        result = service.script_as_delete()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)

    def _test_database_delete_script(self, scripter, service):
        """ Helper function to test delete script for databases """
        # Set up the mocks
        mock_server = Server(self.connection)
        mock_database = Database(mock_server, 'test')

        def database_mock_fn(connection):
            mock_database._template_root = mock.MagicMock(return_value=View.TEMPLATE_ROOT)
            mock_database._delete_query_data = mock.MagicMock(return_value={"data": {"name": "test"}})
            result = mock_database.delete_script(connection)
            return result

        def scripter_mock_fn():
            mock_database.delete_script = mock.MagicMock(return_value=database_mock_fn(self.connection))
            return mock_database.delete_script()

        scripter.get_database_delete_script = mock.MagicMock(return_value=scripter_mock_fn())
        service.script_as_delete = mock.MagicMock(return_value=scripter.get_database_delete_script())

        # If I try to get select script for any object
        result = service.script_as_delete()

        # The result shouldn't be none or an empty string
        self.assertNotNoneOrEmpty(result)


if __name__ == '__main__':
    unittest.main()
