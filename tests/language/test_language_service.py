# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Test connection.ConnectionService"""

import unittest
from unittest.mock import MagicMock

import psycopg2


from pgsqltoolsservice.hosting import (
    JSONRPCServer,
    NotificationContext,
    RequestContext,
    ServiceProvider
)
from pgsqltoolsservice.language import LanguageService
from pgsqltoolsservice.language.contracts import (
    LANGUAGE_FLAVOR_CHANGE_NOTIFICATION, LanguageFlavorChangeParams
)
import tests.utils as utils


class TestLanguageService(unittest.TestCase):
    """Methods for testing the language service"""

    def test_register(self):
        # Setup:
        # ... Create a mock service provider
        server: JSONRPCServer = JSONRPCServer(None, None)
        server.set_notification_handler = MagicMock()
        server.set_request_handler = MagicMock()
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
        nc: NotificationContext = utils.get_mock_notification_context()

        service.handle_flavor_change(nc, pgsql_params)
        service.handle_flavor_change(nc, mssqql_params)
        service.handle_flavor_change(nc, other_params)

        # Then:
        # ... Only non-PGSQL SQL files should be ignored
        nc.send_notification.assert_not_called()
        self.assertFalse(service.is_pgsql_uri(mssqql_params.uri))
        self.assertTrue(service.is_pgsql_uri(pgsql_params.uri))
        self.assertTrue(service.is_pgsql_uri(other_params.uri))

        # When: I change from MSSQL to PGSQL
        mssqql_params = LanguageFlavorChangeParams.from_data('file://msuri.sql', 'sql', 'pgsql')
        service.handle_flavor_change(nc, mssqql_params)

        # Then: the service is updated to allow intellisense 
        self.assertTrue(service.is_pgsql_uri(mssqql_params.uri))
        


