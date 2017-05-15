# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test server.py"""

from __future__ import unicode_literals
import unittest

import mock
from jsonrpc import dispatcher

from pgsqltoolsservice.server import Server


class TestConnectionService(unittest.TestCase):
    """Methods for testing the connection service"""

    def test_server_initialization(self):
        """Test that the server can be initialized"""
        server = Server(None, None)
        result = server.initialize()
        self.assertTrue('version' in dispatcher)
        self.assertTrue('capabilities/list' in dispatcher)
        self.assertIsNotNone(result['capabilities'])

    def test_server_capabilities(self):
        """Test that the server responds to the capabilities/list method"""
        server = Server(None, None)
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

    def test_send_event(self):
        """Test that the send_event method serializes output as expected for JSON RPC"""
        server = Server(None, None)
        server.handle_output = mock.Mock()
        server.send_event('connection/complete', None)
        server.handle_output.assert_called_once_with('{"jsonrpc":"2.0","method":"connection/complete","params":null}')


if __name__ == '__main__':
    unittest.main()
