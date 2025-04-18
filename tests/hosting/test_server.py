# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import time
import unittest
import unittest.mock as mock
from queue import Queue

import tests.utils as utils
from ossdbtoolsservice.hosting import (
    NotificationContext,
    RequestContext,
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.json_reader import StreamJSONRPCReader
from ossdbtoolsservice.hosting.json_writer import StreamJSONRPCWriter
from ossdbtoolsservice.hosting.message_configuration import IncomingMessageConfiguration
from ossdbtoolsservice.hosting.message_server import MessageHandler
from ossdbtoolsservice.hosting.rpc_message_server import (
    RPCMessageServer,
    StreamRPCMessageServer,
)
from ossdbtoolsservice.serialization.serializable import Serializable


class JSONRPCServerTests(unittest.TestCase):
    def test_handler_init(self) -> None:
        # If: I create a Handler class
        handler = MessageHandler("class", "handler")

        # Then: The values should be available
        self.assertEqual(handler.param_class, "class")
        self.assertEqual(handler.handler, "handler")

    def test_server_init(self) -> None:
        # Setup: Create objects to init the server with
        input_stream = io.BytesIO()
        output_stream = io.BytesIO()
        logger = utils.get_mock_logger()

        # If: I create a server
        server = StreamRPCMessageServer(input_stream, output_stream, None, logger=logger)

        # Then: The state should be initialized as defined
        self.assertIsInstance(server.writer, StreamJSONRPCWriter)
        self.assertIsInstance(server.reader, StreamJSONRPCReader)
        self.assertIs(server._logger, logger)
        self.assertEqual(server._version, "1")
        self.assertFalse(server._stop_requested)

        # ... The output queue should be empty
        self.assertIsInstance(server._output_queue, Queue)
        self.assertTrue(server._output_queue.all_tasks_done)
        self.assertDictEqual(server._notification_handlers, {})
        self.assertListEqual(server._shutdown_handlers, [])

        # ... The threads shouldn't have started yet
        self.assertFalse(server._output_thread.is_alive())
        self.assertFalse(server._input_thread.is_alive())

        # ... The built-in handlers should be assigned
        self.assertTrue("echo" in server._request_handlers)
        self.assertIsNotNone(server._request_handlers["echo"])
        self.assertTrue("version" in server._request_handlers)
        self.assertIsNotNone(server._request_handlers["version"].handler)
        self.assertTrue("shutdown" in server._request_handlers)
        self.assertIsNotNone(server._request_handlers["shutdown"].handler)
        self.assertTrue("exit" in server._request_handlers)
        self.assertIsNotNone(server._request_handlers["exit"].handler)

    def test_add_shutdown_handler(self) -> None:
        # If: I add a shutdown handler
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.add_shutdown_handler(handler)

        # Then: The shutdown handlers should contain the handler
        self.assertTrue(handler in server._shutdown_handlers)

    def test_set_request_handler(self) -> None:
        # If: I add a request handler
        params = IncomingMessageConfiguration("test/test", int)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_request_handler(params, handler)

        # Then: The request handler should contain the handler
        self.assertTrue(params.method in server._request_handlers)
        self.assertIsNotNone(server._request_handlers[params.method])
        self.assertIs(server._request_handlers[params.method].param_class, int)
        self.assertIs(server._request_handlers[params.method].handler, handler)

    def test_set_notification_handler(self) -> None:
        # If: I add a notification handler
        params = IncomingMessageConfiguration("test/test", int)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_notification_handler(params, handler)

        # Then: The request handler should contain the handler
        self.assertTrue(params.method in server._notification_handlers)
        self.assertIsNotNone(server._notification_handlers[params.method])
        self.assertIs(server._notification_handlers[params.method].param_class, int)
        self.assertIs(server._notification_handlers[params.method].handler, handler)

    # BUILT-IN HANDLER TESTS ###############################################

    @staticmethod
    def test_echo_request() -> None:
        # If: I send a request for an echo
        rc = utils.MockRequestContext()
        params = {}
        RPCMessageServer._handle_echo_request(rc, params)

        # Then: The params should have been echoed back
        rc.send_response.assert_called_once_with(params)
        rc.send_notification.assert_not_called()
        rc.send_error.assert_not_called()

    @staticmethod
    def test_version_request() -> None:
        # If: I send a request for the version
        rc = utils.MockRequestContext()
        server = utils.MockMessageServer()
        server._handle_version_request(rc, None)

        # Then: I should get a response
        rc.send_response.assert_called_once_with(server._version)
        rc.send_error.assert_not_called()
        rc.send_notification.assert_not_called()

    def test_shutdown_request(self) -> None:
        # If: I send a request for the service to shutdown
        rc = utils.MockRequestContext()
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.add_shutdown_handler(handler)
        server._handle_shutdown_request(rc, None)

        # Then:
        # ... The server should be shutting down
        self.assertTrue(server._stop_requested)

        # ... The shutdown handler should be called
        handler.assert_called_once()

    # RequestContext TESTS #################################################

    def test_request_context_send_response(self) -> None:
        # Setup: Create a request context
        server = utils.MockMessageServer()
        in_message = JSONRPCMessage.from_dictionary(
            {"id": "123", "method": "test/text/", "params": {}}
        )
        rc = RequestContext(in_message.message_id, server)

        # If: I send a response via the response handler
        params = {}
        rc.send_response(params)

        # Then:
        # ... There should be a message in the outbound queue
        self.assertTrue(len(server.sent_messages) == 1)
        out_message = server.sent_messages[0]
        self.assertIsInstance(out_message, JSONRPCMessage)

        # .. The message must be a response with the proper id
        self.assertEqual(out_message.message_type, JSONRPCMessageType.ResponseSuccess)
        self.assertEqual(out_message.message_id, "123")
        self.assertEqual(out_message.message_result, params)

    def test_request_context_send_notification(self) -> None:
        # Setup: Create a request context
        server = utils.MockMessageServer()
        in_message = JSONRPCMessage.from_dictionary(
            {"id": "123", "method": "test/text/", "params": {}}
        )
        rc = RequestContext(in_message.message_id, server)

        # If: I send a notification
        params = {}
        method = "test/test"
        rc.send_notification(method, params)

        # Then:
        # ... There should be a message in the outbound queue
        self.assertTrue(len(server.sent_messages) == 1)
        out_message = server.sent_messages[0]
        self.assertIsInstance(out_message, JSONRPCMessage)

        # .. The message must be a response with the proper id
        self.assertEqual(out_message.message_type, JSONRPCMessageType.Notification)
        self.assertIsNone(out_message.message_id)
        self.assertEqual(out_message.message_params, params)

    def test_request_context_send_error(self) -> None:
        # Setup: Create a request context
        server = utils.MockMessageServer()
        in_message = JSONRPCMessage.from_dictionary(
            {"id": "123", "method": "test/text/", "params": {}}
        )
        rc = RequestContext(in_message.message_id, server)

        # If: I send an error
        params = {}
        rc.send_error(params)

        # Then:
        # ... There should be a message in the outbound queue
        self.assertTrue(len(server.sent_messages) == 1)
        out_message = server.sent_messages[0]
        self.assertIsInstance(out_message, JSONRPCMessage)

        # .. The message must be a response with the proper id
        self.assertEqual(out_message.message_type, JSONRPCMessageType.ResponseError)
        self.assertEqual(out_message.message_id, "123")
        self.assertIsInstance(out_message.message_error, dict)
        self.assertIs(out_message.message_error["message"], params)

    # DISPATCHER TESTS #####################################################

    @staticmethod
    def test_dispatch_invalid() -> None:
        # If: I dispatch an invalid message
        message = JSONRPCMessage("invalidType")
        server = utils.MockMessageServer()
        server._dispatch_message(message)

        # Then: Nothing should have happened

    @staticmethod
    def test_dispatch_request_no_handler() -> None:
        # If: I dispatch a message that has no handler
        logger = utils.get_mock_logger()
        message = JSONRPCMessage.create_request("123", "non_existent", {})
        server = utils.MockMessageServer()
        server._dispatch_message(message)

        # Then:
        # ... Nothing should have happened
        # TODO: Capture that an error was sent
        # ... A warning should have been logged
        logger.warning.assert_called_once()

    def test_dispatch_request_none_class(self) -> None:
        # Setup: Create a server with a single handler that
        # has none for the deserialization class
        config = IncomingMessageConfiguration("test/test", None)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_request_handler(config, handler)

        # If: I dispatch a message that has none set for the deserialization class
        params = {}
        message = JSONRPCMessage.create_request("123", "test/test", params)
        server._dispatch_message(message)

        # Then:
        # ... The handler should have been called
        handler.assert_called_once()

        # ... The parameters to the handler should have been a request context and params
        self.assertIsInstance(handler.mock_calls[0][1][0], RequestContext)
        self.assertIs(handler.mock_calls[0][1][0].message_id, message.message_id)
        self.assertIs(handler.mock_calls[0][1][1], params)

    def test_dispatch_request_normal(self) -> None:
        # Setup: Create a server with a single handler
        # that has none for the deserialization class
        config = IncomingMessageConfiguration("test/test", _TestParams)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_request_handler(config, handler)

        # If: I dispatch a message that has none set for the deserialization class
        params = {}
        message = JSONRPCMessage.create_request("123", "test/test", params)
        server._dispatch_message(message)

        # Then:
        # ... The handler should have been called
        handler.assert_called_once()

        # ... The parameters to the handler should have been a request context and params
        self.assertIsInstance(handler.mock_calls[0][1][0], RequestContext)
        self.assertIs(handler.mock_calls[0][1][0].message_id, message.message_id)
        self.assertIsInstance(handler.mock_calls[0][1][1], _TestParams)

    @staticmethod
    def test_dispatch_notification_no_handler() -> None:
        # If: I dispatch a message that has no handler
        logger = utils.get_mock_logger()
        message = JSONRPCMessage.create_notification("non_existent", {})
        server = utils.MockMessageServer()
        server._dispatch_message(message)

        # Then:
        # ... Nothing should have happened
        # TODO: Capture that an error was sent
        # ... A warning should have been logged
        logger.warning.assert_called_once()

    def test_dispatch_notification_none_class(self) -> None:
        # Setup: Create a server with a single
        # handler that has none for the deserialization class
        config = IncomingMessageConfiguration("test/test", None)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_notification_handler(config, handler)

        # If: I dispatch a message that has none set for the deserialization class
        params = {}
        message = JSONRPCMessage.create_notification("test/test", params)
        server._dispatch_message(message)

        # Then:
        # ... The handler should have been called
        handler.assert_called_once()

        # ... The parameters to the handler should have been a request context and params
        self.assertIsInstance(handler.mock_calls[0][1][0], NotificationContext)
        self.assertIs(handler.mock_calls[0][1][1], params)

    def test_dispatch_notification_normal(self) -> None:
        # Setup: Create a server with a single handler
        # that has none for the deserialization class
        config = IncomingMessageConfiguration("test/test", _TestParams)
        handler = mock.MagicMock()
        server = utils.MockMessageServer()
        server.set_notification_handler(config, handler)

        # If: I dispatch a message that has none set for the deserialization class
        params = {}
        message = JSONRPCMessage.create_notification("test/test", params)
        server._dispatch_message(message)

        # Then:
        # ... The handler should have been called
        handler.assert_called_once()

        # ... The parameters to the handler should have been a request context and params
        self.assertIsInstance(handler.mock_calls[0][1][0], NotificationContext)
        self.assertIsInstance(handler.mock_calls[0][1][1], _TestParams)

    # RequestContext TESTS #################################################

    def test_notification_context_send(self) -> None:
        # Setup: Create a request context
        server = utils.MockMessageServer()
        nc = NotificationContext(server)

        # If: I send a response via the response handler
        method = "test/test"
        params = {}
        nc.send_notification(method, params)

        # Then:
        # ... There should be a message in the outbound queue
        self.assertTrue(len(server.sent_messages) == 1)
        out_message = server.sent_messages[0]
        self.assertIsInstance(out_message, JSONRPCMessage)

        # .. The message must be a response with the proper id
        self.assertEqual(out_message.message_type, JSONRPCMessageType.Notification)
        self.assertIsNone(out_message.message_id)
        self.assertEqual(out_message.message_params, params)
        self.assertEqual(out_message.message_method, method)

    # END-TO-END TESTS #####################################################

    def test_reads_message(self) -> None:
        # Setup:
        # ... Create an input stream with a single message
        input_stream = io.BytesIO(b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}')
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = StreamRPCMessageServer(
            input_stream, output_stream, None, logger=utils.get_mock_logger()
        )

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
        self.assertDictEqual(
            dispatch_mock.mock_calls[0][1][0].dictionary, expected_output.dictionary
        )

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_thread.is_alive())
        self.assertFalse(server._output_thread.is_alive())

    def test_read_multiple_messages(self) -> None:
        # Setup:
        # ... Create an input stream with two messages
        test_bytes = b'Content-Length: 30\r\n\r\n{"method":"test", "params":{}}'
        input_stream = io.BytesIO(test_bytes + test_bytes)
        output_stream = io.BytesIO()

        # ... Create a server that uses the input and output streams
        server = StreamRPCMessageServer(
            input_stream, output_stream, None, logger=utils.get_mock_logger()
        )

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
        self.assertDictEqual(
            dispatch_mock.mock_calls[0][1][0].dictionary, expected_output.dictionary
        )
        self.assertDictEqual(
            dispatch_mock.mock_calls[1][1][0].dictionary, expected_output.dictionary
        )

        # Teardown: All background threads should be shut down.
        self.assertFalse(server._input_thread.is_alive())
        self.assertFalse(server._output_thread.is_alive())


class _TestParams(Serializable):
    @classmethod
    def from_dict(cls, dictionary) -> "_TestParams":
        return _TestParams()

    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
