# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Callable, List, Optional, TypeVar    # noqa
import unittest
import unittest.mock as mock

import json

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.json_rpc_server import RequestContext
import ossdbtoolsservice.utils as utils
from ossdbtoolsservice.utils.telemetry import TelemetryParams


TValidation = TypeVar(Optional[Callable[[any], None]])


class ExpectedMessage:
    def __init__(
            self,
            message_type: JSONRPCMessageType,
            message_method: Optional[str],
            param_type: type,
            validation: TValidation = None
    ):
        self.message_method: str = message_method
        self.message_type: JSONRPCMessageType = message_type
        self.param_type = param_type
        self.validation = validation


class ReceivedMessage:
    def __init__(
            self,
            message_type: JSONRPCMessageType,
            message_method: Optional[str],
            param: any,
            param_type: type,
            rpc_message: JSONRPCMessage
    ):
        self.message_type: JSONRPCMessageType = message_type
        self.message_method: Optional[str] = message_method
        self.param_type: type = param_type
        self.param: any = param
        self.rpc_message: JSONRPCMessage = rpc_message


class ReceivedError:
    def __init__(self, code: int, message: str, data: any):
        self.code = code
        self.message = message
        self.data = data


class RequestFlowValidator:
    def __init__(self):
        self.unittest = unittest.TestCase('__init__')
        self._expected_messages: List[ExpectedMessage] = []
        self._received_messages: List[ReceivedMessage] = []

        # Create a request context and monkey patch all the methods to capture the messages
        self.request_context: RequestContext = RequestContext(None, None)
        self.request_context.send_notification = mock.MagicMock(side_effect=self._received_notification_callback)
        self.request_context.send_response = mock.MagicMock(side_effect=self._received_response_callback)
        self.request_context.send_error = mock.MagicMock(side_effect=self._received_error_callback)

    # METHODS ##############################################################
    def add_expected_error(self, expected_type: type, validation: TValidation = None) -> 'RequestFlowValidator':
        expected_error = ExpectedMessage(JSONRPCMessageType.ResponseError, None, expected_type, validation)
        self._expected_messages.append(expected_error)
        return self

    def add_expected_notification(
            self,
            expected_type: type,
            method: str,
            validation: TValidation = None
    ) -> 'RequestFlowValidator':
        expected_notification = ExpectedMessage(JSONRPCMessageType.Notification, method, expected_type, validation)
        self._expected_messages.append(expected_notification)
        return self

    def add_expected_response(self, expected_type: type, validation: TValidation = None) -> 'RequestFlowValidator':
        expected_response = ExpectedMessage(JSONRPCMessageType.ResponseSuccess, None, expected_type, validation)
        self._expected_messages.append(expected_response)
        return self

    def validate(self):
        # Iterate over the two lists in sync to to see if they are the same
        for i in range(0, max([len(self._expected_messages), len(self._received_messages)])):
            # Step 0) Make sure both messages exist
            if i >= len(self._expected_messages):
                raise Exception(
                    'Unexpected message received: '
                    f'[{self._received_messages[i].message_type}] '
                    f'{self._received_messages[i].param}'
                )
            expected = self._expected_messages[i]

            if i >= len(self._received_messages):
                raise Exception(
                    'Expected additional messages: '
                    f'[{self._expected_messages[i].message_type}] '
                    f'{self._expected_messages[i].param_type}'
                    f'{self._expected_messages[i].message_method}'
                )
            received = self._received_messages[i]

            # Step 1) Make sure the message type matches
            self.unittest.assertIs(received.message_type, expected.message_type)

            # Step 2) Make sure the param type matches
            self.unittest.assertIs(received.param_type, expected.param_type)

            # Step 3) Make sure the message method matches
            self.unittest.assertEqual(received.message_method, expected.message_method)

            # Step 4) Make sure the RPC Message is JSON serializable
            # This catches issues where notification methods are not a strings
            json_content = json.dumps(utils.serialization.convert_to_dict(received.param), sort_keys=True)
            self.unittest.assertIsNotNone(json_content)
            self.unittest.assertNotEqual(json_content, '')

            # Step 5) Make sure the params it passes validation
            self.unittest.assertIsNotNone(received.param)
            if expected.validation is not None:
                expected.validation(received.param)

    # BASIC VALIDATION LOGIC ###############################################
    @staticmethod
    def basic_error_validation(param: ReceivedError) -> None:
        # Make sure there is a message received
        test_case = unittest.TestCase('__init__')
        test_case.assertIsNotNone(param.message)
        test_case.assertNotEqual(param.message.strip(), '')

    @staticmethod
    def validate_telemetry_error(view, name, errorCode) -> TValidation:
        """Returns single paramter function to validate view, name and errorCode of TelemetryParams for
        telemetry error event"""
        def validate_telemetry_error_helper(telemetryParams: TelemetryParams):
            test_case = unittest.TestCase('__init__')
            test_case.assertTrue("eventName" in telemetryParams.params)
            test_case.assertTrue("properties" in telemetryParams.params)
            test_case.assertTrue("measures" in telemetryParams.params)

            properties = telemetryParams.params['properties']

            test_case.assertTrue("view" in properties)
            test_case.assertTrue("name" in properties)
            test_case.assertTrue("errorCode" in properties)
            test_case.assertEqual(properties['view'], view)
            test_case.assertEqual(properties['name'], name)
            test_case.assertEqual(properties['errorCode'], errorCode)
        return validate_telemetry_error_helper

    # IMPLEMENTATION DETAILS ###############################################
    def _received_error_callback(self, message: str, data: any = None, code: int = 0):
        error = ReceivedError(code, message, data)
        rpc_message = JSONRPCMessage.create_error(0, code, message, data)
        received_message = ReceivedMessage(JSONRPCMessageType.ResponseError, None, error, type(data), rpc_message)
        self._received_messages.append(received_message)

    def _received_notification_callback(self, method: str, params: any):
        rpc_message = JSONRPCMessage.create_notification(method, params)
        received_message = ReceivedMessage(JSONRPCMessageType.Notification, method, params, type(params), rpc_message)
        self._received_messages.append(received_message)

    def _received_response_callback(self, params: any):
        rpc_message = JSONRPCMessage.create_response(0, params)
        received_message = ReceivedMessage(JSONRPCMessageType.ResponseSuccess, None, params, type(params), rpc_message)
        self._received_messages.append(received_message)
