# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing expected JSON RPC input/outputs when the tools service is being used"""

import io
import json
import logging
import os
import queue
import re
import time
import unittest
from unittest import mock

import pgsqltoolsservice.pgtoolsservice_main as pgtoolsservice_main
from pgsqltoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from tests.integration import get_connection_details, integration_test


class RPCMessage:
    request_id = 0

    def __init__(self, method: str, params: str, message_type: JSONRPCMessageType):
        self.method = method
        self.params = json.loads(params) if params is not None else None
        self.message_type = message_type
        if self.message_type is JSONRPCMessageType.Request:
            self.request_id = RPCMessage.request_id
            RPCMessage.request_id += 1

    def __str__(self):
        message_dictionary = {
            'jsonrpc': '2.0',
            'method': self.method
        }
        if self.params is not None:
            message_dictionary['params'] = self.params
        if self.message_type is JSONRPCMessageType.Request:
            message_dictionary['id'] = self.request_id
        return json.dumps(message_dictionary)


class EndToEndIntegrationTests(unittest.TestCase):

    @integration_test
    def test_all(self):
        server, input_stream, output_stream, log_stream, output_bytes_written = self.start_service()
        error_connection_details = get_connection_details()
        error_connection_details['dbname'] += '_error'
        test_messages = [
            self.initialize(),
            self.version(),
            self.change_configuration(),
            self.list_capabilities(),
            self.connection_request('error_connection', error_connection_details),
            self.connection_request('good_connection', get_connection_details()),
            self.shutdown()]
        flat_messages = []
        for message in test_messages:
            if not isinstance(message, list):
                flat_messages.append(message)
            else:
                flat_messages.extend(message)
        requests = []
        for message in flat_messages:
            bytes_message = b'Content-Length: ' + str.encode(str(len(str(message)))) + b'\r\n\r\n' + str.encode(str(message))
            input_stream.write(bytes_message)
            input_stream.flush()
            if message.message_type is JSONRPCMessageType.Request:
                requests.append(message)
        server.wait_for_exit()
        # Dequeue any remaining messages if needed
        try:
            while True:
                last_message = server._output_queue.get_nowait()
                if last_message is not None:
                    server.writer.send_message(last_message)
        except queue.Empty:
            pass

        print(log_stream.getvalue())
        # print(output_stream.read(output_bytes_written[0]))
        output = output_stream.read(output_bytes_written[0]).decode()
        messages = re.split(r'Content-Length: .+\s+', output)
        result_dict = {}
        for message_str in messages:
            if not message_str:
                continue
            print('\n\n\n\n\n')
            print(message_str)
            message = json.loads(message_str.strip())
            if 'id' in message:
                result_dict[message['id']] = message['result']
        # Verify that each request has a response
        for request in requests:
            if request.method == 'shutdown':
                continue
            self.assertIn(request.request_id, result_dict)

    def start_service(self):
        # Set up the server's input and output
        input_r, input_w = os.pipe()
        output_r, output_w = os.pipe()
        server_input_stream = open(input_r, 'rb', buffering=0, closefd=False)
        server_output_stream = open(output_w, 'wb', buffering=0, closefd=False)
        server_output_stream.close = mock.Mock()
        test_input_stream = open(input_w, 'wb', buffering=0, closefd=False)
        test_output_stream = open(output_r, 'rb', buffering=0, closefd=False)
        output_bytes_written = [0]

        # Mock the server output stream's write method so that the test knows how many bytes have been written
        def mock_write(message):
            output_bytes_written[0] += len(message)
            return mock.DEFAULT
        server_output_stream.write = mock.Mock(side_effect=mock_write, wraps=server_output_stream.write)

        log_stream = io.StringIO()
        logger = logging.Logger('test')
        logger.addHandler(logging.StreamHandler(log_stream))
        server = pgtoolsservice_main._create_server(server_input_stream, server_output_stream, logger)
        server.start()
        return server, test_input_stream, test_output_stream, log_stream, output_bytes_written

    def initialize(self):
        return RPCMessage(
            'initialize',
            '{"processId": 4340, "capabilities": {}, "trace": "off"}',
            JSONRPCMessageType.Request
        )

    def version(self):
        return RPCMessage('version', None, JSONRPCMessageType.Request)

    def change_configuration(self):
        return RPCMessage(
            'workspace/didChangeConfiguration',
            '{"settings":{"pgsql":{"logDebugInfo":false,"enabled":true,"defaultDatabase":"postgres","format":{"keywordCase":null,"identifierCase":null,"stripComments":false,"reindent":true}}}}',  # noqa
            JSONRPCMessageType.Notification
        )

    def list_capabilities(self):
        return RPCMessage(
            'capabilities/list',
            '{"hostName":"carbon","hostVersion":"1.0"}',
            JSONRPCMessageType.Request
        )

    def connection_request(self, owner_uri, connection_options):
        connection_request = RPCMessage(
            'connection/connect',
            '{"ownerUri":"%s","connection":{"options":%s}}' % (owner_uri, json.dumps(connection_options)),
            JSONRPCMessageType.Request
        )
        language_flavor_notification = RPCMessage(
            'connection/languageflavorchanged',
            '{"uri":"%s","language":"sql","flavor":"PGSQL"}' % owner_uri,
            JSONRPCMessageType.Notification
        )
        return [connection_request, language_flavor_notification]

    def shutdown(self):
        return RPCMessage('shutdown', None, JSONRPCMessageType.Request)
