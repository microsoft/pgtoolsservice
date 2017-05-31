# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time
import io

from mock import call, MagicMock

from pgsqltoolsservice.hosting import JsonRpcServer, JsonRpcMessage


class JsonRpcServerTests(unittest.TestCase):

    def test_request_enqueued(self):
        """
            Verify requests are enqueued.
        """
        input_stream = io.BytesIO()
        output_stream = io.BytesIO(b'sample output')

        test_client = JsonRpcServer(input_stream, output_stream)
        test_client.send_request(u'test/test', {'test': 'test'})

        request = test_client._output_queue.get()

        self.assertEqual(request.message_method, u'test/test')
        self.assertDictEqual(request.message_params, {'test': 'test'})

    def test_reads_message(self):
        """
            Verify input was read.
        """
        # Setup:
        # ... Create an input stream with a single message
        input_stream = io.BytesIO(b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}')
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = JsonRpcServer(input_stream, output_stream)

        # ... Patch the server to not dispatch a message
        dispatch_mock = MagicMock()
        server._dispatch_message = dispatch_mock

        # If: I start the server, run it for a bit, and stop it
        server.start()
        time.sleep(1)
        server.stop()
        time.sleep(.1)

        # Then: The dispatch method should have been called
        expected_output = JsonRpcMessage.from_dictionary({"method": "test", "params": {}})
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
        server = JsonRpcServer(input_stream, output_stream)

        # ... Patch the server to not dispatch a message
        dispatch_mock = MagicMock()
        server._dispatch_message = dispatch_mock

        # If: I start the server, run it for a bit, and stop it
        server.start()
        time.sleep(1)
        server.stop()
        time.sleep(.1)

        # Then: The dispatch method should have been called
        expected_output = JsonRpcMessage.from_dictionary({"method": "test", "params": {}})
        msg_call = call(expected_output)
        dispatch_mock.assert_has_calls([msg_call, msg_call])

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_consumer.isAlive())
        self.assertFalse(server._output_consumer.isAlive())


if __name__ == u'__main__':
    unittest.main()
