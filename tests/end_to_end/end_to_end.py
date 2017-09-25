# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module for testing expected JSON RPC input/outputs when the tools service is being used"""

import io
import json
import threading
import unittest

import pgsqltoolsservice.pgtoolsservice_main as pgtoolsservice_main
from pgsqltoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from tests.integration import get_connection_details, integration_test


class RPCMessage:
    request_id = 0

    def __init__(self, method: str, params: str, message_type: JSONRPCMessageType):
        self.method = method
        self.params = json.loads(params)
        self.message_type = message_type
        if self.message_type is JSONRPCMessageType.Request:
            self.request_id = RPCMessage.request_id
            RPCMessage.request_id += 1

    def __str__(self):
        message_dictionary = {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': self.params
        }
        if self.message_type is JSONRPCMessageType.Request:
            message_dictionary['id'] = self.request_id
        return json.dumps(message_dictionary)


class EndToEndIntegrationTests(unittest.TestCase):

    def test_all(self):
        server, input_stream, output_stream = self.start_service()
        input_stream.write(self.initialize())
        self.change_configuration()
        self.list_capabilities()
        error_connection_details = get_connection_details()
        error_connection_details['dbname'] += '_error'
        self.connection_request('error_connection', error_connection_details)
        self.connection_request('good_connection', get_connection_details())

    def start_service(self):
        input_stream = io.StringIO()
        output_stream = io.StringIO()
        server = pgtoolsservice_main._create_server(input_stream, output_stream, None)
        server.start()
        return server, input_stream, output_stream

    def initialize(self):
        return RPCMessage(
            'initialize',
            '{"processId": 4340, "capabilities": {}, "trace": "off"}',
            JSONRPCMessageType.Request
        )

    def change_configuration(self):
        return RPCMessage(
            'workspace/didChangeConfiguration',
            '{"settings":{"pgsql":{"logDebugInfo":false,"enabled":true,"defaultDatabase":"postgres","format":{"keywordCase":null,"identifierCase":null,"stripComments":false,"reindent":true}}}}',  # noqa
            JSONRPCMessageType.Request
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
            '{"ownerUri":"%s","connection":{"options":%s}}' % (owner_uri, connection_options),
            JSONRPCMessageType.Request
        )
        language_flavor_notification = RPCMessage(
            'connection/languageflavorchanged',
            '{"uri":"%s","language":"sql","flavor":"PGSQL"}}' % owner_uri,
            JSONRPCMessageType.Notification
        )
        return [connection_request, language_flavor_notification]
