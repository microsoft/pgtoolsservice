# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test server.py"""

import unittest
from pgsqltoolsservice.server import Server
from jsonrpc import dispatcher


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_server_initialization(self):
        """Test that the server can be initialized"""
        server = Server()
        result = server.initialize()
        self.assertTrue('version' in dispatcher)
        self.assertTrue('capabilities/list' in dispatcher)
        self.assertIsNotNone(result['capabilities'])

    def test_server_capabilities(self):
        """Test that the server responds to the capabilities/list method"""
        server = Server()
        server.initialize()
        result = dispatcher['capabilities/list']('Test Host', '1.0')
        # Validate the response
        self.assertTrue('capabilities' in result)
        capabilities = result['capabilities']
        self.assertTrue('protocolVersion' in capabilities)
        self.assertTrue('providerName' in capabilities)
        self.assertTrue('providerDisplayName' in capabilities)
        self.assertTrue('connectionProvider' in capabilities)
        connection_provider = capabilities['connectionProvider']
        self.assertTrue('options' in connection_provider)
        options = connection_provider['options']
        self.assertTrue(len(options) > 0)
        for option in options:
            self.assertTrue('name' in option)


if __name__ == '__main__':
    unittest.main()
