# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from typing import Any
from unittest import mock

import tests.utils as utils
from ossdbtoolsservice.connection import ConnectionService, PooledConnection
from ossdbtoolsservice.connection.contracts import ConnectionCompleteParams
from ossdbtoolsservice.hosting import ServiceProvider
from ossdbtoolsservice.scripting.contracts.script_as_request import (
    ScriptAsParameters,
    ScriptAsResponse,
    ScriptOperation,
)
from ossdbtoolsservice.scripting.scripter import Scripter
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.utils.constants import CONNECTION_SERVICE_NAME
from tests.mock_request_validation import RequestFlowValidator
from tests.pgsmo_tests.utils import MockPGServerConnection

"""Module for testing the scripting service"""


class TestScriptingService(unittest.TestCase):
    """Methods for testing the scripting service"""

    MOCK_URI = "testuri"
    MOCK_SCRIPT = "script"

    def test_init(self) -> None:
        # If: I create a new scripting service
        ss: ScriptingService = ScriptingService()

        # Then:
        # ... The service should have its internal state initialized
        self.assertIsNone(ss._service_provider)

    def test_registration(self) -> None:
        # Setup:
        # ... Create a mock service provider
        server = utils.MockMessageServer()
        server.set_notification_handler = mock.MagicMock()
        server.set_request_handler = mock.MagicMock()
        sp: ServiceProvider = ServiceProvider(server, {}, utils.get_mock_logger())

        # If: I register a scripting service
        ss: ScriptingService = ScriptingService()
        ss.register(sp)

        # Then:
        # ... The service should have registered its request handlers
        server.set_request_handler.assert_called()
        server.set_notification_handler.assert_not_called()

        # ... The service provider should have been stored
        self.assertIs(ss._service_provider, sp)

    def test_handle_scriptas_missing_params(self) -> None:
        # Setup: Create a scripting service
        ss = ScriptingService()
        ss._service_provider = utils.get_mock_service_provider({})

        # If: I make a scripting request missing params
        rc: RequestFlowValidator = RequestFlowValidator()
        rc.add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        ss._handle_script_as_request(rc.request_context, None)

        # Then:
        # ... I should get an error response
        rc.validate()

    def test_handle_scriptas_invalid_operation(self) -> None:
        # Setup: Create a scripting service
        mock_connection = {}
        cs = ConnectionService()
        cs.connect = mock.MagicMock(
            return_value=ConnectionCompleteParams(owner_uri=TestScriptingService.MOCK_URI)
        )
        pooled_connection = PooledConnection(lambda _: mock_connection, lambda _: None)
        cs.get_pooled_connection = mock.MagicMock(return_value=pooled_connection)
        ss = ScriptingService()
        ss._service_provider = utils.get_mock_service_provider({CONNECTION_SERVICE_NAME: cs})

        # If: I create an OE session with missing params
        rc: RequestFlowValidator = RequestFlowValidator()
        rc.add_expected_error(type(None), RequestFlowValidator.basic_error_validation)
        ss._handle_script_as_request(rc.request_context, None)

        # Then:
        # ... I should get an error response
        rc.validate()

    def test_handle_scriptas_successful_operation(self) -> None:
        # NOTE: There's no need to test all types here, the scripter tests should handle this

        # Setup:
        # ... Create a scripting service
        mock_connection = MockPGServerConnection()
        cs = ConnectionService()
        cs.connect = mock.MagicMock(
            return_value=ConnectionCompleteParams(owner_uri=TestScriptingService.MOCK_URI)
        )

        def get_pooled_connection(*args: Any, **kwargs: Any) -> PooledConnection:
            return PooledConnection(lambda _: mock_connection, lambda _: None)

        cs.get_pooled_connection = mock.MagicMock(side_effect=get_pooled_connection)
        ss = ScriptingService()
        ss._service_provider = utils.get_mock_service_provider({CONNECTION_SERVICE_NAME: cs})

        # ... Create validation logic for responses
        def validate_response(response: ScriptAsResponse) -> None:
            self.assertEqual(response.owner_uri, TestScriptingService.MOCK_URI)
            self.assertEqual(response.script, TestScriptingService.MOCK_SCRIPT)

        # ... Create a scripter with mocked out calls
        patch_path = "ossdbtoolsservice.scripting.scripting_service.Scripter"
        with mock.patch(patch_path) as scripter_patch:
            mock_scripter: Scripter = Scripter(mock_connection)
            mock_scripter.script = mock.MagicMock(
                return_value=TestScriptingService.MOCK_SCRIPT
            )
            scripter_patch.return_value = mock_scripter

            scripting_object = {
                "metadata_type_name": "Table",
                "name": "test_table",
                "schema": "test_schema",
            }

            # For each operation supported
            for operation in ScriptOperation:
                # If: I request to script
                rc: RequestFlowValidator = RequestFlowValidator()
                rc.add_expected_response(ScriptAsResponse, validate_response)

                params = ScriptAsParameters.from_dict(
                    {
                        "ownerUri": TestScriptingService.MOCK_URI,
                        "operation": operation,
                        "scripting_objects": [scripting_object],
                    }
                )

                ss._handle_script_as_request(rc.request_context, params)

                # Then:
                # ... The request should have been handled correctly
                rc.validate()

            # ... All of the scripter methods should have been called once
            matches = {operation: 0 for operation in ScriptOperation}
            for call_args in mock_scripter.script.call_args_list:
                matches[call_args[0][0]] += 1

            for calls in matches.values():
                self.assertEqual(calls, 1)
