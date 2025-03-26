# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from tests.integration import get_connection_details, integration_test
from tests.json_rpc_tests import DefaultRPCTestMessages, JSONRPCTestCase


class LanguageServiceIntelliSenseJSONRPCTests(unittest.TestCase):
    @integration_test
    def test_refresh_successful(self):
        # If I set up a valid connection
        owner_uri = "test_uri"
        connection_details = get_connection_details()
        connection_request, language_flavor_notification = (
            DefaultRPCTestMessages.connection_request(owner_uri, connection_details)
        )

        # And I request that intellisense be refreshed
        intelli_ready = DefaultRPCTestMessages.intellisense_refresh(owner_uri)

        # Expect the textDocument/intelliSenseReady notification to be sent
        test_case = JSONRPCTestCase(
            [connection_request, language_flavor_notification, intelli_ready]
        )
        test_case.run()
