# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing expected JSON RPC input/outputs when the tools service is being used"""

import io
import json
import logging
import os
import re
import threading
from typing import Callable, List, Optional, Tuple
from unittest import mock

from ossdbtoolsservice.hosting.json_message import JSONRPCMessageType
import ossdbtoolsservice.ossdbtoolsservice_main as ossdbtoolsservice_main
from ossdbtoolsservice.utils import constants


class RPCTestMessage:
    """
    Class representing an individual JSON RPC message sent as part of an end-to-end integration test

    :param method: The name of the JSON RPC method (e.g. 'connection/connect')
    :param message_type: The JSONRpcMessageType for the message
    :param expect_error_response: Whether the server will respond to this message with an error.
    This parameter will be ignored for non-request messages. Default is False.
    :param response_verifier: An optional callback that will be called with the response object,
    which can be used to verify that the response is the expected one. This parameter will be
    ignored for non-request messages. For request messages, if this is not provided, the test will
    verify that some response was sent, but will not verify its details.
    :param notification_verifiers: An optional list of verifiers that can be used to verify that
    the server sent the expected notifications following this message. Each verifier is a tuple
    where the first element is a filter function to determine if a given notification was sent in
    response to this message, and the second element is an optional verifier that will be called
    for each notification that the filter function returns True for. If the message causes the
    server to send back notifications, this argument must be provided.
    """
    request_id = 0

    def __init__(self, method: str, params: str, message_type: JSONRPCMessageType, expect_error_response: bool = False,
                 response_verifier: Callable[[dict], None] = None,
                 notification_verifiers: List[Tuple[Callable[[dict], bool], Optional[Callable[[dict], None]]]] = None):
        self.method = method
        self.params = json.loads(params) if params is not None else None
        self.message_type = message_type
        if self.message_type is JSONRPCMessageType.Request:
            self.request_id = None
        self.expect_error_response = expect_error_response
        self.response_verifier = response_verifier
        self.notification_verifiers = notification_verifiers

    def initialize_request_id(self):
        """For a request message, initialize its request ID"""
        if self.message_type is not JSONRPCMessageType.Request:
            raise RuntimeError('initialize_request_id can only be called on request messages')
        elif self.request_id is not None:
            raise RuntimeError('Request ID already initialized')
        self.request_id = RPCTestMessage.request_id
        RPCTestMessage.request_id += 1

    def __str__(self):
        message_dictionary = {
            'jsonrpc': '2.0',
            'method': self.method
        }
        if self.params is not None:
            message_dictionary['params'] = self.params
        if self.message_type is JSONRPCMessageType.Request:
            if self.request_id is None:
                self.initialize_request_id()
            message_dictionary['id'] = self.request_id
        return json.dumps(message_dictionary)


class JSONRPCTestCase:
    def __init__(self, test_messages: List[RPCTestMessage]):
        initialization_messages = [
            DefaultRPCTestMessages.initialize(),
            DefaultRPCTestMessages.version(),
            DefaultRPCTestMessages.change_configuration(),
            DefaultRPCTestMessages.list_capabilities()]
        shutdown_messages = [DefaultRPCTestMessages.shutdown()]
        self.messages = initialization_messages + test_messages + shutdown_messages

    def run(self):
        # Start the server
        input_stream, output_stream, output_info = JSONRPCTestCase.start_service()
        output = ""

        # Send all messages to the server
        for message in self.messages:
            expected_write_calls = output_info[0] + 2 * ((len(message.notification_verifiers) if message.notification_verifiers is not None else 0) +
                                                         (1 if message.message_type is JSONRPCMessageType.Request else 0))
            bytes_message = b'Content-Length: ' + str.encode(str(len(str(message)))) + b'\r\n\r\n' + str.encode(str(message))
            output_info[1].acquire()
            input_stream.write(bytes_message)
            input_stream.flush()
            if message.method == 'shutdown':
                continue
            output_info[1].wait_for(lambda: output_info[0] >= expected_write_calls, 10)
            if output_info[0] < expected_write_calls:
                raise RuntimeError(f'Timed out waiting for response or notification for method {message.method}')

        # Process the output into responses and notifications
        output = output_stream.getvalue().decode()
        messages = re.split(r'Content-Length: .+\s+', output)
        response_dict = {}
        notifications = []
        for message_str in messages:
            if not message_str:
                continue
            message = json.loads(message_str.strip())
            if 'id' in message:
                message_id = message['id']
                if message_id in response_dict:
                    raise RuntimeError(f'Server sent multiple responses with ID {message_id}')
                response_dict[message_id] = message
            else:
                notifications.append(message)

        # Verify that each request has a response
        requests = [message for message in self.messages if message.message_type is JSONRPCMessageType.Request]
        responses_to_verify = {response['id'] for response in response_dict.values()}
        for request in requests:
            if request.method == 'shutdown':
                continue
            response = response_dict.get(request.request_id)
            if response is None:
                raise RuntimeError(f'Request ID {request.request_id} (method {request.method}) has no response')
            # Verify that the response is or is not an error, as expected
            if request.expect_error_response:
                if 'error' not in response:
                    raise RuntimeError(f'Expected error response to request method {request.method} but got \n{json.dumps(response)}')
            else:
                if 'result' not in response:
                    raise RuntimeError(f'Expected successful response to request method {request.method} but got \n{json.dumps(response)}')
            # Run the response verifier if present
            responses_to_verify.remove(response['id'])
            if request.response_verifier is not None:
                request.response_verifier(response)
        if responses_to_verify:
            raise RuntimeError('Server sent the following responses that had no corresponding request:\n{}'.format('\n'.join(
                [json.dumps(response_dict[response_id]) for response_id in responses_to_verify])))

        # Verify the notifications
        notifications_to_verify = {index for index, _ in enumerate(notifications)}
        for message in self.messages:
            verifiers = message.notification_verifiers
            if not verifiers:
                continue
            for filter_function, verification_function in verifiers:
                filtered_notifications = [(index, notification) for index, notification in enumerate(notifications) if filter_function(notification)]
                notification_count = len(filtered_notifications)
                if notification_count == 0:
                    raise RuntimeError(f'Expected 1 notification for request with method {message.method} but got 0')
                # If there was more than 1 notification matching the filter, take the first one that matches
                index = None
                notification = None
                for filtered_notification in filtered_notifications:
                    index = filtered_notification[0]
                    notification = filtered_notification[1]
                    if index in notifications_to_verify:
                        break
                notifications_to_verify.remove(index)
                if verification_function is not None:
                    verification_function(notification)
        if notifications_to_verify:
            raise RuntimeError('Server sent the following unexpected notifications:\n{}'.format('\n'.join(
                [json.dumps(notifications[index]) for index in notifications_to_verify])))

    @staticmethod
    def start_service():
        # Set up the server's input and output
        input_r, input_w = os.pipe()
        server_input_stream = open(input_r, 'rb', buffering=0, closefd=False)
        test_input_stream = open(input_w, 'wb', buffering=0, closefd=False)
        server_output_stream = io.BytesIO()
        server_output_stream.close = mock.Mock()
        output_info = [0, threading.Condition()]  # Number of times write called, Condition variable for monitoring info

        # Mock the server output stream's write method so that the test knows how many messages have been written
        old_write_method = server_output_stream.write

        def mock_write(message):
            output_info[1].acquire()
            bytes_written = old_write_method(message)
            output_info[0] += 1
            output_info[1].notify()
            output_info[1].release()
            return bytes_written
        server_output_stream.write = mock.Mock(side_effect=mock_write)

        logger = logging.Logger('test')
        logger.addHandler(logging.NullHandler())
        server = ossdbtoolsservice_main._create_server(server_input_stream, server_output_stream, logger, constants.PG_PROVIDER_NAME)
        server.start()
        return test_input_stream, server_output_stream, output_info


class DefaultRPCTestMessages:
    @staticmethod
    def initialize():
        return RPCTestMessage(
            'initialize',
            '{"processId": 4340, "capabilities": {}, "trace": "off"}',
            JSONRPCMessageType.Request
        )

    @staticmethod
    def version():
        return RPCTestMessage('version', None, JSONRPCMessageType.Request)

    @staticmethod
    def change_configuration():
        return RPCTestMessage(
            'workspace/didChangeConfiguration',
            '{"settings":{"pgsql":{"logDebugInfo":false,"enabled":true,"defaultDatabase":"postgres","format":{"keywordCase":null,"identifierCase":null,"stripComments":false,"reindent":true}}}}',  # noqa
            JSONRPCMessageType.Notification
        )

    @staticmethod
    def list_capabilities():
        return RPCTestMessage(
            'capabilities/list',
            '{"hostName":"carbon","hostVersion":"1.0"}',
            JSONRPCMessageType.Request
        )

    @staticmethod
    def connection_request(owner_uri, connection_options):
        connection_request = RPCTestMessage(
            'connection/connect',
            '{"ownerUri":"%s","connection":{"options":%s}}' % (owner_uri, json.dumps(connection_options)),
            JSONRPCMessageType.Request,
            notification_verifiers=[(
                lambda notification: notification['method'] == 'connection/complete' and notification['params']['ownerUri'] == owner_uri,
                None
            )]
        )
        language_flavor_notification = RPCTestMessage(
            'connection/languageflavorchanged',
            '{"uri":"%s","language":"sql","flavor":"PGSQL"}' % owner_uri,
            JSONRPCMessageType.Notification,
            notification_verifiers=[(
                lambda notification: notification['method'] == 'textDocument/intelliSenseReady' and notification['params']['ownerUri'] == owner_uri,
                None
            )]
        )
        return (connection_request, language_flavor_notification)

    @staticmethod
    def shutdown():
        return RPCTestMessage('shutdown', None, JSONRPCMessageType.Request)
