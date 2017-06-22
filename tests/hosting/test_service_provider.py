# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import unittest.mock as mock

from pgsqltoolsservice.hosting.json_rpc_server import JSONRPCServer
from pgsqltoolsservice.hosting.service_provider import ServiceProvider
import tests.utils as utils


class TestServiceProvider(unittest.TestCase):
    def test_init(self):
        # If: I create a new service provider
        server = JSONRPCServer(None, None)
        logger = utils.get_mock_logger()
        mock_service = mock.MagicMock(return_value={})
        services = {'service_name': mock_service}
        sp = ServiceProvider(server, services, logger)

        # Then:
        # ... The properties should return the values I set (server/logger)
        self.assertFalse(sp._is_initialized)
        self.assertIs(sp._server, server)
        self.assertIs(sp.server, server)
        self.assertIs(sp._logger, logger)
        self.assertIs(sp.logger, logger)

        # ... The services should be transformed and called
        self.assertIsInstance(sp._services, dict)
        self.assertTrue('service_name' in sp._services)
        mock_service.assert_called_once()

    def test_initialize_already_initialized(self):
        # Setup: Create a service provider and initialize it once
        sp = self._get_service_provider()
        sp.initialize()

        # If: I attempt to initialize it again
        # Then: An exception should be raised
        with self.assertRaises(RuntimeError):
            sp.initialize()

    def test_initialize(self):
        # Setup: Create a service provider with a couple services
        sp = self._get_service_provider(2)

        # If: I attempt to initialize it
        sp.initialize()

        # Then: The services should all have been initialized with the service provider
        for (service_name, service_instance) in sp._services.items():
            self.assertTrue(service_instance.has_initialized)
            self.assertIs(service_instance.service_provider, sp)

    def test_get_service_not_initialized(self):
        # Setup: Create a service provider that hasn't been initialized
        sp = self._get_service_provider()

        # If: I attempt to get a service
        # Then: An exception should be thrown
        with self.assertRaises(RuntimeError):
            sp['service']

    def test_get_service(self):
        # Setup: Create a service provider that has been initialized
        sp = self._get_service_provider()

        # If: I attempt to get a service
        sp.initialize()
        service = sp['service_name0']

        # Then: I should get the service back
        self.assertIsInstance(service, TestServiceProvider._TestService)

    # IMPLEMENTATION DETAILS ###############################################
    class _TestService:
        def __init__(self):
            self.has_initialized = False
            self.service_provider = None

        def register(self, service_provider):
            self.has_initialized = True
            self.service_provider = service_provider

    @staticmethod
    def _get_service_provider(services: int=1) -> ServiceProvider:
        # If: I create a new service provider
        server = JSONRPCServer(None, None)
        logger = utils.get_mock_logger()
        services = {'service_name' + str(x): TestServiceProvider._TestService for x in range(0, services)}
        sp = ServiceProvider(server, services, logger)

        return sp
