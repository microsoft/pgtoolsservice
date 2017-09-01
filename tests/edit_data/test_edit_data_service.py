# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from queue import Queue
from unittest import mock
import tests.utils as utils
from unittest.mock import patch

from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.edit_data.edit_data_service import EditDataService
from tests.mocks.service_provider_mock import ServiceProviderMock
from pgsqltoolsservice.edit_data.contracts import UpdateCellRequest, InitializeEditParams
from pgsqltoolsservice.hosting.json_message import JSONRPCMessage
from pgsqltoolsservice.hosting import RequestContext
from pgsqltoolsservice.connection import ConnectionService
from pgsqltoolsservice.query_execution.query_execution_service import QueryExecutionService


class TestEditDataService(unittest.TestCase):

    def setUp(self):
        self._service_under_test = EditDataService()
        self._service_provider = ServiceProviderMock({'query_execution': {}})

        self.cursor = utils.MockCursor(None)
        self.connection = utils.MockConnection(cursor=self.cursor)
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

    @patch('pgsqltoolsservice.edit_data.edit_data_service.DataEditorSession')
    def test_initialization(self, mockdataeditorsession):
        queue = Queue()
        message = JSONRPCMessage.from_dictionary({'id': '123', 'method': 'edit/initialize', 'params': {}})
        request_context = RequestContext(message, queue)
        self._service_under_test._edit_initialize(request_context, self._initialize_edit_request)
        mockdataeditorsession.assert_called()

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

        update_cell_request = UpdateCellRequest()
        update_cell_request.owner_uri = 'test_owner_uri'
        update_cell_request.row_id = 1
        update_cell_request.column_id = 1
        update_cell_request.new_value = 'Updates'

        request_context = utils.MockRequestContext()

        edit_session = mock.MagicMock()
        edit_session.update_cell = mock.Mock(return_value='Something')

        self._service_under_test._active_sessions[update_cell_request.owner_uri] = edit_session

        self._service_under_test._update_cell(request_context, update_cell_request)

        edit_session.update_cell.assert_called()

        args = edit_session.update_cell.call_args[0]

        self.assertEqual(update_cell_request.row_id, args[0])
        self.assertEqual(update_cell_request.column_id, args[1])
        self.assertEqual(update_cell_request.new_value, args[2])

    def test_edit_initialize(self):
        request_context = utils.MockRequestContext()
        params = None

        edit_session = mock.MagicMock()
        edit_session._edit_initialize(request_context, params)
        edit_session._edit_initialize.assert_called()


if __name__ == '__main__':
    unittest.main()
