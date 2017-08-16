# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from pgsqltoolsservice.edit_data.edit_data_service import EditDataService
from tests.mocks.service_provider_mock import ServiceProviderMock


class TestEditDataService(unittest.TestCase):

    def setUp(self):
        self._service_under_test = EditDataService()
        self._service_provider = ServiceProviderMock()
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


if __name__ == '__main__':
    unittest.main()
