# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import unittest.mock as mock

from pgsqltoolsservice.capabilities import CapabilitiesService
from pgsqltoolsservice.capabilities.contracts import InitializeResult, CapabilitiesResult
from pgsqltoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.workspace import WorkspaceService
import tests.utils as utils


class TestCapabilitiesService(unittest.TestCase):
    """Methods for testing the capabilities service"""

    def test_initialization(self):
        # Setup: Create a capabilities service with a mocked out service provider
        mock_server_set_request = mock.MagicMock()
        mock_server = JSONRPCServer(None, None)
        mock_server.set_request_handler = mock_server_set_request
        mock_service_provider = ServiceProvider(mock_server, {}, None)
        service = CapabilitiesService()

        # If: I initialize the service
        service.register(mock_service_provider)

        # Then:
        # ... There should have been request handlers set
        mock_server_set_request.assert_called()

        # ... Each mock call should have an IncomingMessageConfig and a function pointer
        for mock_call in mock_server_set_request.mock_calls:
            self.assertIsInstance(mock_call[1][0], IncomingMessageConfiguration)
            self.assertTrue(callable(mock_call[1][1]))

    # noinspection PyUnresolvedReferences
    def test_initialization_request(self):
        # Setup: Create a request context with mocked out send_* methods
        rc = utils.MockRequestContext()

        # If: I request the language service capabilities of this server
        CapabilitiesService._handle_initialize_request(rc, None)

        # Then: A response should have been sent that is a Capabilities result
        rc.send_notification.assert_not_called()
        rc.send_error.assert_not_called()
        rc.send_response.assert_called_once()
        self.assertIsInstance(rc.send_response.mock_calls[0][1][0], InitializeResult)

    # noinspection PyUnresolvedReferences
    def test_dmp_capabilities_request(self):
        # Setup: Create a request context with mocked out send_* methods and set up the capabilities service
        rc = utils.MockRequestContext()
        capabilities_service = CapabilitiesService()
        workspace_service = WorkspaceService()
        capabilities_service._service_provider = utils.get_mock_service_provider({constants.WORKSPACE_SERVICE_NAME: workspace_service})

        # If: I request the dmp capabilities of this server
        capabilities_service._handle_dmp_capabilities_request(rc, None)

        # Then: A response should have been sent that is a Capabilities result
        rc.send_notification.assert_not_called()
        rc.send_error.assert_not_called()
        rc.send_response.assert_called_once()
        self.assertIsInstance(rc.send_response.mock_calls[0][1][0], CapabilitiesResult)

    def test_dmp_capabilities_have_backup_options(self):
        """Test that the capabilities returned for a DMP capabilities request include backup options"""
        # Setup: Create a request context with mocked out send_* methods and set up the capabilities service
        rc = utils.MockRequestContext()
        capabilities_service = CapabilitiesService()
        workspace_service = WorkspaceService()
        capabilities_service._service_provider = utils.get_mock_service_provider({constants.WORKSPACE_SERVICE_NAME: workspace_service})

        # If: I request the dmp capabilities of this server
        capabilities_service._handle_dmp_capabilities_request(rc, None)

        # Then: The response should include backup capabilities
        rc.send_response.assert_called_once()
        capabilities_result = rc.send_response.mock_calls[0][1][0]
        features = capabilities_result.capabilities.features
        backup_options_list = [feature for feature in features if feature.feature_name == 'backup']
        # There should be exactly one feature containing backup options
        self.assertEqual(len(backup_options_list), 1)
        backup_options = backup_options_list[0]
        # The backup options should be enabled
        self.assertTrue(backup_options.enabled)
        # And the backup options should contain at least 1 option
        self.assertGreater(len(backup_options.options_metadata), 0)


if __name__ == '__main__':
    unittest.main()
