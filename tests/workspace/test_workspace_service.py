# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock

from pgsqltoolsservice.hosting import ServiceProvider, JSONRPCServer
from pgsqltoolsservice.workspace import WorkspaceService, PGSQLConfiguration
from pgsqltoolsservice.workspace.workspace import Workspace


class TestWorkspaceService(unittest.TestCase):
    """Tests of the workspace service"""

    def test_init(self):
        # If: I create a new workspace service
        ws: WorkspaceService = WorkspaceService()

        # Then:
        # ... The service should have configuration and expose it via the propery
        self.assertIsInstance(ws._configuration, PGSQLConfiguration)
        self.assertIs(ws.configuration, ws._configuration)

        # ... The service should have a workspace
        self.assertIsInstance(ws._workspace, Workspace)

        # ... The service should define callback lists
        self.assertListEqual(ws._config_change_callbacks, [])
        self.assertListEqual(ws._text_change_callbacks, [])
        self.assertListEqual(ws._text_open_callbacks, [])
        self.assertListEqual(ws._text_close_callbacks, [])

    def test_register(self):
        # Setup:
        # ... Create a mock service provider
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = MagicMock()
        server.set_request_handler = MagicMock()
        sp: ServiceProvider = ServiceProvider(server, {}, None)

        # If: I register a workspace service
        ws: WorkspaceService = WorkspaceService()
        ws.register(sp)

        # Then:
        # ... The notifications should have been registered
        server.set_notification_handler.assert_called()
        server.set_request_handler.assert_not_called()

        # ... The service provider should have been stored
        self.assertIs(ws._service_provider, sp)

    def test_register_callbacks(self):
        # Setup:
        # ... Create a workspace service
        ws: WorkspaceService = WorkspaceService()

        # ... Create the list of methods to test and the list of handlers to check
        test_methods = [
            (ws.register_config_change_callback, ws._config_change_callbacks),
            (ws.register_text_change_callback, ws._text_change_callbacks),
            (ws.register_text_close_callback, ws._text_close_callbacks),
            (ws.register_text_open_callback, ws._text_open_callbacks)
        ]
        test_callback = MagicMock()

        # If: I
