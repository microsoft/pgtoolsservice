# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import unittest.mock as mock

from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.capabilities.contracts import InitializeResult, CapabilitiesResult
from ossdbtoolsservice.hosting import JSONRPCServer, ServiceProvider, IncomingMessageConfiguration
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME
from ossdbtoolsservice.workspace import WorkspaceService

import tests.utils as utils


class TestCapabilitiesService(unittest.TestCase):
    """Methods for testing the capabilities service"""

    def test_initialization(self):
        # Setup: Create a capabilities service with a mocked out service provider
        mock_server_set_request = mock.MagicMock()
        mock_server = JSONRPCServer(None, None)
        mock_server.set_request_handler = mock_server_set_request
        mock_service_provider = ServiceProvider(mock_server, {}, MYSQL_PROVIDER_NAME, None)
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


if __name__ == '__main__':
    unittest.main()
