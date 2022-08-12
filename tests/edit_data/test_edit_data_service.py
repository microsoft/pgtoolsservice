# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from queue import Queue
from unittest import mock
import tests.utils as utils
from unittest.mock import patch

from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from tests.mocks.service_provider_mock import ServiceProviderMock
from ossdbtoolsservice.edit_data.contracts import (
    UpdateCellRequest, CreateRowRequest, SessionOperationRequest, DeleteRowRequest, RevertCellRequest,
    RevertRowRequest, EditCommitRequest, DisposeRequest, InitializeEditParams
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting import RequestContext
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.query_execution.query_execution_service import QueryExecutionService


class TestEditDataService(unittest.TestCase):

    def setUp(self):
        self._service_under_test = EditDataService()
        self._mock_connection = mock.MagicMock()
        self._service_provider = ServiceProviderMock({'query_execution': {}, 'connection': self._mock_connection})

        self.cursor = utils.MockPsycopgCursor(None)
        self.connection = utils.MockPsycopgConnection(cursor=self.cursor)
        self.cursor.connection = self.connection
        self.connection_service = ConnectionService()
        self.connection_service.get_connection = mock.Mock(return_value=self.connection)
        self.query_execution_service = QueryExecutionService()
        self._service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service,
                                            constants.QUERY_EXECUTION_SERVICE_NAME: self.query_execution_service}
        self._service_provider._is_initialized = True

        self._service_under_test.register(self._service_provider)

        # self._connection = MockConnection({"port": "8080", "host": "test", "dbname": "test"})
        self._initialize_edit_request = InitializeEditParams()

        self._initialize_edit_request.schema_name = 'public'
        self._initialize_edit_request.object_name = 'Employee'
        self._initialize_edit_request.object_type = 'Table'
        self._initialize_edit_request.owner_uri = 'testuri'

    @patch('ossdbtoolsservice.edit_data.edit_data_service.DataEditorSession')
    def test_initialization(self, mockdataeditorsession):
        queue = Queue()
        message = JSONRPCMessage.from_dictionary({'id': '123', 'method': 'edit/initialize', 'params': {}})
        request_context = RequestContext(message, queue)
        self._service_under_test._edit_initialize(request_context, self._initialize_edit_request)
        mockdataeditorsession.assert_called()

    def test_initialization_with_none_as_schema_param(self):
        request_context = RequestContext(None, None)
        self._initialize_edit_request.schema_name = None
        errormsg = 'Parameter schema_name contains a None, empty, or whitespace string'
        self.assert_exception_on_method_call(ValueError, errormsg, self._service_under_test._edit_initialize, request_context, self._initialize_edit_request)

    def test_initialization_with_none_as_owner_uri(self):
        request_context = RequestContext(None, None)
        self._initialize_edit_request.owner_uri = None
        errormsg = 'Parameter owner_uri contains a None, empty, or whitespace string'

        self.assert_exception_on_method_call(ValueError, errormsg, self._service_under_test._edit_initialize, request_context, self._initialize_edit_request)

    def test_initialization_with_empty_object_name(self):
        request_context = RequestContext(None, None)
        self._initialize_edit_request.object_name = ' '
        errormsg = 'Parameter object_name contains a None, empty, or whitespace string'

        self.assert_exception_on_method_call(ValueError, errormsg, self._service_under_test._edit_initialize, request_context, self._initialize_edit_request)

    def test_initialization_with_empty_object_type(self):
        request_context = RequestContext(None, None)
        self._initialize_edit_request.object_type = ' '
        errormsg = 'Parameter object_type contains a None, empty, or whitespace string'

        self.assert_exception_on_method_call(ValueError, errormsg, self._service_under_test._edit_initialize, request_context, self._initialize_edit_request)

    def assert_exception_on_method_call(self, exception_type: type, exception_message: str, method_to_call: object, *args) -> None:
        '''asserts if a method call raises 'exceptiontype' exception or not'''
        with self.assertRaises(exception_type, msg=exception_message) as context_manager:
            method_to_call(*args)

        if context_manager.exception.args is not None:
            self.assertEquals(exception_message, context_manager.exception.args[0])

    def test_register_should_initlialize_states(self):
        self.assertEqual(self._service_under_test._service_provider, self._service_provider)
        self.assertEqual(self._service_under_test._logger, self._service_provider.logger)

    def test_register_should_log_service_initialized(self):
        self._service_provider.logger.info.assert_called_with('Edit data service successfully initialized')

    def test_register_should_set_request_handler_for_service_actions(self):
        self._service_provider.server.set_request_handler.assert_called()

    def test_update_cell_with_no_active_session(self):

        update_cell_request = UpdateCellRequest()
        update_cell_request.owner_uri = 'test_owner_uri'

        request_context = utils.MockRequestContext()

        with self.assertRaises(KeyError):
            self._service_under_test._update_cell(request_context, update_cell_request)

    def test_update_cell_with_active_session(self):

        request = UpdateCellRequest()
        request.owner_uri = 'test_owner_uri'
        request.row_id = 1
        request.column_id = 1
        request.new_value = 'Updates'

        self._validate_row_operations(
            self._service_under_test._update_cell, 'update_cell', request,
            request.row_id, request.column_id, request.new_value)

    def test_create_row_operation(self):

        request = CreateRowRequest()
        request.owner_uri = 'test_owner_uri'

        self._validate_row_operations(self._service_under_test._create_row, 'create_row', request, None)

    def test_delete_row_operation(self):

        request = DeleteRowRequest()
        request.owner_uri = 'test_owner_uri'
        request.row_id = 1

        self._validate_row_operations(self._service_under_test._delete_row, 'delete_row', request, request.row_id)

    def test_revert_row_operation(self):

        request = RevertRowRequest()
        request.owner_uri = 'test_owner_uri'
        request.row_id = 1

        self._validate_row_operations(self._service_under_test._revert_row, 'revert_row', request, request.row_id)

    def test_revert_cell_operation(self):

        request = RevertCellRequest()
        request.owner_uri = 'test_owner_uri'
        request.row_id = 1
        request.column_id = 1

        self._validate_row_operations(self._service_under_test._revert_cell, 'revert_cell', request, request.row_id, request.column_id)

    def test_dispose_when_edit_session_available(self):
        request_context = utils.MockRequestContext()
        edit_session = mock.MagicMock()

        request = DisposeRequest()
        request.owner_uri = 'owner_uri'

        self._service_under_test._active_sessions[request.owner_uri] = edit_session

        self._service_under_test._dispose(request_context, request)

        self.assertEqual(0, len(self._service_under_test._active_sessions))

    def test_dispose_when_edit_session_is_not_available(self):
        request_context = utils.MockRequestContext()

        request = DisposeRequest()
        request.owner_uri = 'owner_uri'

        self._service_under_test._dispose(request_context, request)

        self.assertEqual(request_context.last_error_message, 'Edit data session not found')

    def test_commit_when_edit_session_is_not_available(self):
        request_context = utils.MockRequestContext()

        request = EditCommitRequest()
        request.owner_uri = 'owner_uri'

        edit_session = mock.MagicMock()
        self._service_under_test._active_sessions[request.owner_uri] = edit_session

        self._service_under_test._edit_commit(request_context, request)

        args = edit_session.commit_edit.call_args[0]

        success_callback = args[1]

        success_callback()

        request_context.send_response.assert_called_once()

        failure_callback = args[2]

        error_message = 'Test error'

        failure_callback(error_message)

        self.assertEqual(error_message, request_context.last_error_message)

    def _validate_row_operations(self, handler, edit_session_method_name: str, request_params: SessionOperationRequest, *args):

        request_context = utils.MockRequestContext()
        edit_session = mock.MagicMock()
        self._service_under_test._active_sessions[request_params.owner_uri] = edit_session

        handler(request_context, request_params)

        edit_session_call = getattr(edit_session, edit_session_method_name)

        edit_session_call.assert_called_once()

        actual_call_args = edit_session_call.call_args[0]

        for index, arg in enumerate(args):
            if arg is not None:
                self.assertEqual(arg, actual_call_args[index])

    def test_edit_initialize(self):
        request_context = utils.MockRequestContext()
        params = None

        edit_session = mock.MagicMock()
        edit_session._edit_initialize(request_context, params)
        edit_session._edit_initialize.assert_called()


class TestMySQLEditDataService(TestEditDataService):

    def setUp(self):
        self._service_under_test = EditDataService()
        self._mock_connection = mock.MagicMock()
        self._service_provider = ServiceProviderMock({'query_execution': {}, 'connection': self._mock_connection})

        self.cursor = utils.MockPsycopgCursor(None)
        self.connection = utils.MockPyMySQLConnection()
        self.connection.cursor = self.cursor
        self.cursor.connection = self.connection
        self.connection_service = ConnectionService()
        self.connection_service.get_connection = mock.Mock(return_value=self.connection)
        self.query_execution_service = QueryExecutionService()
        self._service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service,
                                            constants.QUERY_EXECUTION_SERVICE_NAME: self.query_execution_service}
        self._service_provider._is_initialized = True

        self._service_under_test.register(self._service_provider)

        self._initialize_edit_request = InitializeEditParams()

        self._initialize_edit_request.schema_name = 'public'
        self._initialize_edit_request.object_name = 'Employee'
        self._initialize_edit_request.object_type = 'Table'
        self._initialize_edit_request.owner_uri = 'testuri'


if __name__ == '__main__':
    unittest.main()
