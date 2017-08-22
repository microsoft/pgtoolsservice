# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from unittest import mock

from pgsqltoolsservice.edit_data.edit_data_service import EditDataService
from tests.mocks.service_provider_mock import ServiceProviderMock
from pgsqltoolsservice.edit_data.contracts import UpdateCellRequest
import tests.utils as utils


class TestEditDataService(unittest.TestCase):

    def setUp(self):
        self._service_under_test = EditDataService()
        self._service_provider = ServiceProviderMock({'query_execution': {}})
        self._service_under_test.register(self._service_provider)

    def test_initialization(self):
        """ Just a construct for now. Will add to it as we build further """
        pass

    def test_register_should_initlialize_states(self):
        self.assertEqual(self._service_under_test._service_provider, self._service_provider)
        self.assertEqual(self._service_under_test._logger, self._service_provider.logger)

    def test_register_should_log_service_initialized(self):
        self._service_provider.logger.info.assert_called_with('Edit data service successfully initialized')

    def test_register_should_set_request_handler_for_service_actions(self):
        self._service_provider.server.set_request_handler.assert_called()

    def test_edit_initialize_logs_for_now(self):
        self._service_under_test._edit_initialize({}, {})
        self._service_provider.logger.info.assert_called_with('Calling query')

    def test_edit_subset_logs_for_now(self):
        self._service_under_test._edit_subset({}, {})
        self._service_provider.logger.info.assert_called_with('Edit subset')

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


if __name__ == '__main__':
    unittest.main()
