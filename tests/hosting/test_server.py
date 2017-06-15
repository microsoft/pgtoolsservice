# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time
import io

import mock

from pgsqltoolsservice.hosting.json_rpc_server import JSONRPCServer, IncomingMessageConfiguration
from pgsqltoolsservice.hosting.json_message import JSONRPCMessage


class JSONRPCServerTests(unittest.TestCase):

    def test_request_enqueued(self):
        # Setup: Create empty io streams
        input_stream = io.BytesIO()
        output_stream = io.BytesIO()

        # If: I submit an outbound request
        test_client = JSONRPCServer(input_stream, output_stream)
        test_client.send_request('test/test', {'test': 'test'})

        # Then:
        # ... There should be one request in the outbound queue
        request = test_client._output_queue.get()

        # ... The queued message should match the request we sent
        self.assertEqual(request.message_method, 'test/test')
        self.assertDictEqual(request.message_params, {'test': 'test'})

    def test_reads_message(self):
        # Setup:
        # ... Create an input stream with a single message
        input_stream = io.BytesIO(b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}')
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = JSONRPCServer(input_stream, output_stream)

        # ... Patch the server to not dispatch a message
        dispatch_mock = mock.MagicMock()
        server._dispatch_message = dispatch_mock

        # If: I start the server, run it for a bit, and stop it
        # TODO: Remove explicit sleep and add spin-locks
        server.start()
        time.sleep(1)
        server.stop()
        server.wait_for_exit()

        # Then: The dispatch method should have been called
        expected_output = JSONRPCMessage.from_dictionary({"method": "test", "params": {}})
        dispatch_mock.assert_called_once_with(expected_output)

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_consumer.isAlive())
        self.assertFalse(server._output_consumer.isAlive())

    def test_read_multiple_messages(self):
        # Setup:
        # ... Create an input stream with a single message
        test_bytes = b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}'
        input_stream = io.BytesIO(test_bytes + test_bytes)
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = JSONRPCServer(input_stream, output_stream)

        # ... Patch the server to not dispatch a message
        dispatch_mock = mock.MagicMock()
        server._dispatch_message = dispatch_mock

        # If: I start the server, run it for a bit, and stop it
        server.start()
        time.sleep(1)
        server.stop()
        server.wait_for_exit()

        # Then: The dispatch method should have been called
        expected_output = JSONRPCMessage.from_dictionary({"method": "test", "params": {}})
        msg_call = mock.call(expected_output)
        dispatch_mock.assert_has_calls([msg_call, msg_call])

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_consumer.isAlive())
        self.assertFalse(server._output_consumer.isAlive())

    def test_dispatch_request(self):
        """Test dispatching a request message"""
        server = JSONRPCServer(None, None)

        # Set up the mock handler for the request
        method_name = 'test/method'
        handler = mock.Mock()
        mock_class = mock.Mock()
        deserialized_object = object()
        mock_class.from_dict = mock.Mock(return_value=deserialized_object)
        server.set_request_handler(IncomingMessageConfiguration(method_name, mock_class), handler)

        # Send the message
        message_params = {'testParam': 'test_value'}
        message = JSONRPCMessage.create_request(0, method_name, message_params)
        server._dispatch_message(message)

        # Verify that the params object was converted and that the handler was called
        mock_class.from_dict.assert_called_once_with(message_params)
        handler.assert_called_once_with(mock.ANY, deserialized_object)

    def test_dispatch_notification(self):
        """Test dispatching a notification message"""
        server = JSONRPCServer(None, None)

        # Set up the mock handler for the request
        method_name = 'test/method'
        handler = mock.Mock()
        mock_class = mock.Mock()
        deserialized_object = object()
        mock_class.from_dict = mock.Mock(return_value=deserialized_object)
        server.set_notification_handler(IncomingMessageConfiguration(method_name, mock_class), handler)

        # Send the message
        message_params = {'testParam': 'test_value'}
        message = JSONRPCMessage.create_notification(method_name, message_params)
        server._dispatch_message(message)

        # Verify that the params object was converted and that the handler was
        # called
        mock_class.from_dict.assert_called_once_with(message_params)
        handler.assert_called_once_with(mock.ANY, deserialized_object)

    def test_dispatch_no_handler(self):
        """Test dispatching a message that has no handler"""
        server = JSONRPCServer(None, None)

        # Set up the message
        method_name = 'test/method'
        message_params = {'testParam': 'test_value'}
        message = JSONRPCMessage.create_notification(method_name, message_params)

        # Send the message. There should be no error
        server._dispatch_message(message)


if __name__ == '__main__':
    unittest.main()
