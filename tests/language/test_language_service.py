# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

import unittest
from unittest import mock
import psycopg2

from pgsqltoolsservice.workspace.contracts.common import TextDocumentPosition
from pgsqltoolsservice.hosting import (
    JSONRPCServer,
    NotificationContext,
    RequestContext,
    ServiceProvider
)
from pgsqltoolsservice.language import LanguageService
from pgsqltoolsservice.language.contracts import (
    LanguageFlavorChangeParams
)
from pgsqltoolsservice.utils import constants
from pgsqltoolsservice.workspace import WorkspaceService, PGSQLConfiguration
import tests.utils as utils


class TestLanguageService(unittest.TestCase):
    """Methods for testing the language service"""

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.mock_server_set_request = None
        self.mock_server: JSONRPCServer = None
        self.mock_service_provider: ServiceProvider = None
        self.mock_workspace: WorkspaceService = None
        self.default_text_position: TextDocumentPosition = None


    def setUp(self):
        """Constructor"""
        self.mock_server_set_request = mock.MagicMock()
        self.mock_server = JSONRPCServer(None, None)
        self.mock_server.set_request_handler = self.mock_server_set_request
        self.mock_workspace = mock.Mock()
        services = {constants.WORKSPACE_SERVICE_NAME: self.mock_workspace}
        self.mock_service_provider = ServiceProvider(self.mock_server, services, None)
        self.mock_service_provider._is_initialized = True
        self.default_text_position = TextDocumentPosition.from_dict({
            'text_document': {
                'uri': 'file://my.sql'
            },
            'position':  {
                'line': 1,
                'character': 1
            }
        })

    def test_register(self):
        """Test registration of the service"""
        # Setup:
        # ... Create a mock service provider
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = mock.MagicMock()
        server.set_request_handler = mock.MagicMock()
        provider: ServiceProvider = ServiceProvider(server, {}, utils.get_mock_logger())

        # If: I register a language service
        service: LanguageService = LanguageService()
        service.register(provider)

        # Then:
        # ... The notifications should have been registered
        server.set_notification_handler.assert_called()
        server.set_request_handler.assert_called()

        # ... The service provider should have been stored
        self.assertIs(service._service_provider, provider) # noqa

    def test_completion_intellisense_off(self):
        """
        Test that the completion handler returns empty if the intellisense
        is disabled
        """
        # If: intellisense is disabled
        context: RequestContext = utils.MockRequestContext()
        self.mock_workspace.configuration = PGSQLConfiguration()
        self.mock_workspace.configuration.intellisense.enable_intellisense = False
        service: LanguageService = self._init_service()

        # When: I request completion item
        service.handle_completion_request(context, self.default_text_position)

        # Then: 
        # ... An empty completion should be sent over the notification
        context.send_response.asssert_called_once()
        self.assertEqual(context.last_response_params, [])
        # ... and workspace service should not have been queried
        self.mock_workspace.get_text.assert_not_called()

    def test_default_completion_items(self):
        """
        Test that the completion handler returns a set of default values
        when not connected to any URI
        """
        
    def test_language_flavor(self):
        """
        Test that the service ignores files registered as being for non-PGSQL flavors
        """
        # If: I create a new language service
        pgsql_params = LanguageFlavorChangeParams.from_data('file://pguri.sql', 'sql', 'pgsql')
        mssqql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', 'mssql')
        other_params = LanguageFlavorChangeParams.from_data('file://other.doc', 'doc', '')
        service = LanguageService()

        # When: I notify of language preferences
        context: NotificationContext = utils.get_mock_notification_context()

        service.handle_flavor_change(context, pgsql_params)
        service.handle_flavor_change(context, mssqql_params)
        service.handle_flavor_change(context, other_params)

        # Then:
        # ... Only non-PGSQL SQL files should be ignored
        context.send_notification.assert_not_called()
        self.assertFalse(service.is_pgsql_uri(mssqql_params.uri))
        self.assertTrue(service.is_pgsql_uri(pgsql_params.uri))
        self.assertTrue(service.is_pgsql_uri(other_params.uri))

        # When: I change from MSSQL to PGSQL
        mssqql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', 'pgsql')
        service.handle_flavor_change(context, mssqql_params)

        # Then: the service is updated to allow intellisense
        self.assertTrue(service.is_pgsql_uri(mssqql_params.uri))

    def _init_service(self) -> LanguageService:
        service = LanguageService()
        service.register(self.mock_service_provider)
        return service


