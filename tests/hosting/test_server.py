# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
from queue import Queue
import time
import unittest
import unittest.mock as mock

from pgsqltoolsservice.hosting.json_rpc_server import JSONRPCServer, IncomingMessageConfiguration
from pgsqltoolsservice.hosting.json_message import JSONRPCMessage
from pgsqltoolsservice.hosting.json_reader import JSONRPCReader
from pgsqltoolsservice.hosting.json_writer import JSONRPCWriter
import tests.utils as utils


class JSONRPCServerTests(unittest.TestCase):

    def test_handler_init(self):
        # If: I create a Handler class
        handler = JSONRPCServer.Handler('class', 'handler')

        # Then: The values should be available
        self.assertEqual(handler.class_, 'class')
        self.assertEqual(handler.handler, 'handler')

    def test_server_init(self):
        # Setup: Create objects to init the server with
        input_stream = io.BytesIO()
        output_stream = io.BytesIO()
        logger = utils.get_mock_logger()

        # If: I create a server
        server = JSONRPCServer(input_stream, output_stream, logger=logger)

        # Then: The state should be initialized as defined
        self.assertIsInstance(server.writer, JSONRPCWriter)
        self.assertIsInstance(server.reader, JSONRPCReader)
        self.assertIs(server._logger, logger)
        self.assertEqual(server._version, '0')
        self.assertFalse(server._stop_requested)

        # ... The output queue should be empty
        self.assertIsInstance(server._output_queue, Queue)
        self.assertTrue(server._output_queue.all_tasks_done)
        self.assertDictEqual(server._notification_handlers, {})
        self.assertListEqual(server._shutdown_handlers, [])

        # ... The threads shouldn't be assigned yet
        self.assertIsNone(server._output_consumer)
        self.assertIsNone(server._input_consumer)

        # ... The built-in handlers should be assigned
        self.assertTrue('echo' in server._request_handlers)
        self.assertIsNotNone(server._request_handlers['echo'])
        self.assertTrue('version' in server._request_handlers)
        self.assertIsNotNone(server._request_handlers['version'].handler)
        self.assertTrue('shutdown' in server._request_handlers)
        self.assertIsNotNone(server._request_handlers['shutdown'].handler)
        self.assertTrue('exit' in server._request_handlers)
        self.assertIsNotNone(server._request_handlers['exit'].handler)

    def test_add_shutdown_handler(self):
        # If: I add a shutdown handler
        handler = mock.MagicMock()
        server = JSONRPCServer(None, None)
        server.add_shutdown_handler(handler)

        # Then: The shutdown handlers should contain the handler
        self.assertTrue(handler in server._shutdown_handlers)

    def test_set_request_handler(self):
        # If: I add a request handler
        params = IncomingMessageConfiguration('test/test', int)
        handler = mock.MagicMock()
        server = JSONRPCServer(None, None)
        server.set_request_handler(params, handler)

        # Then: The request handler should contain the handler
        self.assertTrue(params.method in server._request_handlers)
        self.assertIsNotNone(server._request_handlers[params.method])
        self.assertIs(server._request_handlers[params.method].class_, int)
        self.assertIs(server._request_handlers[params.method].handler, handler)

    def test_set_notification_handler(self):
        # If: I add a notification handler
        params = IncomingMessageConfiguration('test/test', int)
        handler = mock.MagicMock()
        server = JSONRPCServer(None, None)
        server.set_notification_handler(params, handler)

        # Then: The request handler should contain the handler
        self.assertTrue(params.method in server._notification_handlers)
        self.assertIsNotNone(server._notification_handlers[params.method])
        self.assertIs(server._notification_handlers[params.method].class_, int)
        self.assertIs(server._notification_handlers[params.method].handler, handler)

    # BUILT-IN HANDLER TESTS ###############################################

    def test_echo_request(self):
        # If: I send a

    # END-TO-END TESTS #####################################################

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
        server = JSONRPCServer(input_stream, output_stream, logger=utils.get_mock_logger())

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
        dispatch_mock.assert_called_once()
        self.assertDictEqual(dispatch_mock.mock_calls[0][1][0].dictionary, expected_output.dictionary)

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_consumer.isAlive())
        self.assertFalse(server._output_consumer.isAlive())

    def test_read_multiple_messages(self):
        # Setup:
        # ... Create an input stream with two messages
        test_bytes = b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}'
        input_stream = io.BytesIO(test_bytes + test_bytes)
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = JSONRPCServer(input_stream, output_stream, logger=utils.get_mock_logger())

        # ... Patch the server to not dispatch a message
        dispatch_mock = mock.MagicMock()
        server._dispatch_message = dispatch_mock

        # If: I start the server, run it for a bit, and stop it
        server.start()
        time.sleep(1)
        server.stop()
        server.wait_for_exit()

        # Then: The dispatch method should have been called twice
        expected_output = JSONRPCMessage.from_dictionary({"method": "test", "params": {}})
        self.assertEqual(len(dispatch_mock.mock_calls), 2)
        self.assertDictEqual(dispatch_mock.mock_calls[0][1][0].dictionary, expected_output.dictionary)
        self.assertDictEqual(dispatch_mock.mock_calls[1][1][0].dictionary, expected_output.dictionary)

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_consumer.isAlive())
        self.assertFalse(server._output_consumer.isAlive())


if __name__ == '__main__':
    unittest.main()
