# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock

from pgsqltoolsservice.hosting import JSONRPCServer, NotificationContext, ServiceProvider
from pgsqltoolsservice.workspace import WorkspaceService, PGSQLConfiguration
from pgsqltoolsservice.workspace.workspace import Workspace
from pgsqltoolsservice.workspace.contracts import (
    DidChangeConfigurationParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams
)
import tests.utils as utils


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

        for test_param in test_methods:
            # If: I register a callback with the workspace service
            test_param[0](test_callback)

            # Then: The callback list should be updated
            self.assertListEqual(test_param[1], [test_callback])

    def test_handle_did_change_config(self):
        # Setup: Create a workspace service with two mock config change handlers
        ws: WorkspaceService = WorkspaceService()
        ws._config_change_callbacks = [MagicMock(), MagicMock()]

        # If: The workspace receives a config change notification
        nc: NotificationContext = utils.get_mock_notification_context()
        params: DidChangeConfigurationParams = DidChangeConfigurationParams.from_dict({
            'settings': {
                'pgsql': {
                    'setting': 'NonDefault'
                }
            }
        })
        ws._handle_did_change_config(nc, params)

        # Then:
        # ... No notifications should have been sent
        nc.send_notification.assert_not_called()

        # ... The config should have been updated
        self.assertIs(ws.configuration, params.settings.pgsql)

        # ... The mock config change callbacks should have been called
        for callback in ws._config_change_callbacks:
            callback.assert_called_once_with(params.settings.pgsql)

    def test_handle_text_notification_none(self):
        # Setup:
        # ... Create a workspace service with a mock callbacks and a workspace that always returns None
        ws: WorkspaceService = WorkspaceService()
        ws._text_change_callbacks = [MagicMock()]
        ws._text_open_callbacks = [MagicMock()]
        ws._text_close_callbacks = [MagicMock()]

        workspace: Workspace = Workspace()
        workspace.get_file = MagicMock(returns=None)
        workspace.open_file = MagicMock(returns=None)
        workspace.close_file = MagicMock(returns=None)
        ws._workspace = workspace

        nc: NotificationContext = utils.get_mock_notification_context()

        # ... Create a list of methods call and parameters to call them with
        test_calls = [
            (
                ws._handle_did_change_text_doc,
                self._get_change_text_doc_params(),
                ws._text_change_callbacks[0]
            ),
            (
                ws._handle_did_open_text_doc,
                self._get_open_text_doc_params(),
                ws._text_open_callbacks[0]
            ),
            (
                ws._handle_did_close_text_doc,
                self._get_close_text_doc_params(),
                ws._text_close_callbacks[0]
            )
        ]

        for call in test_calls:
            # If: The workspace service receives a request to handle a file that shouldn't be processed
            call[0](nc, call[1])

            # Then: The associated notification callback should not have been called
            call[2].assert_not_called()


    @staticmethod
    def _get_change_text_doc_params() -> DidChangeTextDocumentParams:
        return DidChangeTextDocumentParams.from_dict({
            'textDocument': {
                'uri': 'someUri',
                'version': 1
            },
            'contentChanges': [
                {
                    'range': {
                        'start': {'line': 1, 'character': 1},
                        'end': {'line': 2, 'character': 3},
                    },
                    'rangeLength': 6,
                    'text': 'abcdefg'
                }
            ]
        })

    @staticmethod
    def _get_close_text_doc_params() -> DidCloseTextDocumentParams:
        return DidCloseTextDocumentParams.from_dict({
            'textDocument': {
                'uri': 'someUri',
                'languageId': 'SQL',
                'version': 2,
                'text': 'abcdef'
            }
        })

    @staticmethod
    def _get_open_text_doc_params() -> DidOpenTextDocumentParams:
        return DidOpenTextDocumentParams.from_dict({
            'textDocument': {
                'uri': 'someUri',
                'languageId': 'SQL',
                'version': 1,
                'text': 'abcdef'
            }
        })
