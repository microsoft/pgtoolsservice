# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from queue import Queue
import threading
import uuid

from pgsqltoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from pgsqltoolsservice.hosting.json_reader import JSONRPCReader
from pgsqltoolsservice.hosting.json_writer import JSONRPCWriter


class JSONRPCServer:
    """
    Handles async requests, async notifications, and async responses
    """
    # CONSTANTS ############################################################
    OUTPUT_THREAD_NAME = u"JSON_RPC_Output_Thread"
    INPUT_THREAD_NAME = u"JSON_RPC_Input_Thread"

    class Handler:
        def __init__(self, class_, handler):
            self.class_ = class_
            self.handler = handler

    def __init__(self, in_stream, out_stream, logger=None):
        self.writer = JSONRPCWriter(out_stream)
        self.reader = JSONRPCReader(in_stream)
        self._logger = logger
        self._stop_requested = False

        self._output_queue = Queue()

        self._request_handlers = {}
        self._notification_handlers = {}

        self._output_consumer = None
        self._input_consumer = None

    # METHODS ##############################################################

    def start(self):
        """
        Starts the background threads to listen for responses and requests from the underlying
        streams. Encapsulated into its own method for future async extensions without threads
        """
        if self._logger is not None:
            self._logger.info(u"JSON RPC server starting...")

        self._output_consumer = threading.Thread(
            target=self._consume_output,
            name=self.OUTPUT_THREAD_NAME
        )
        self._output_consumer.daemon = True
        self._output_consumer.start()

        self._input_consumer = threading.Thread(
            target=self._consume_input,
            name=self.INPUT_THREAD_NAME
        )
        self._input_consumer.daemon = True
        self._input_consumer.start()

    def stop(self):
        """
        Signal request thread to close as soon as possible
        """
        self._stop_requested = True

        # Enqueue None to optimistically unblock background threads so they can check for the cancellation flag
        self._output_queue.put(None)

        # Wait for request thread to finish with a timeout in seconds
        self._input_consumer.join(1)

        # Close the underlying writer
        self.writer.close()
        if self._logger is not None:
            self._logger.info(u"JSON RPC server stopped")

    def send_request(self, method, params):
        """
        Add a new request to the output queue
        :param method: Method string of the request
        :param params: Data to send along with the request
        """
        message_id = str(uuid.uuid4())

        # Create the message
        message = JSONRPCMessage.create_request(message_id, method, params)

        # TODO: Add support for handlers for the responses
        # Add the message to the output queue
        self._output_queue.put(message)

    def set_request_handler(self, method, class_, handler):
        self._request_handlers[method] = self.Handler(class_, handler)

    def set_notification_handler(self, method, class_, handler):
        self._notification_handlers[method] = self.Handler(class_, handler)

    # IMPLEMENTATION DETAILS ###############################################

    def _consume_input(self):
        """
        Listen for messages from the input stream and dispatch them to the registered listeners
        :raises ValueError: The stream was closed. Exit the thread immediately.
        :raises LookupError: No void header with content-length was found
        :raises EOFError: The stream may not contain any bytes yet, so retry.
        """
        if self._logger is not None:
            self._logger.info(u"Input thread started")

        while not self._stop_requested:
            try:
                message = self.reader.read_message()
                self._dispatch_message(message)

            except EOFError as error:
                # Thread fails once we read EOF. Halt the input thread
                self._log_exception(error, self.INPUT_THREAD_NAME)
                break
            except ValueError as error:
                # Stream was closed. Halt the input thread
                self._log_exception(error, self.INPUT_THREAD_NAME)
                break
            except LookupError as error:
                # Content-Length header was not found
                self._log_exception(error, self.INPUT_THREAD_NAME)
                # Do not halt the input thread
            except Exception as error:
                # Catch generic exceptions
                self._log_exception(error, self.INPUT_THREAD_NAME)
                # Do not halt the input thread

    def _consume_output(self):
        """
        Send output over the output stream
        """
        while not self._stop_requested:
            try:
                # Block until queue contains a message to send
                message = self._output_queue.get()
                if message is not None:
                    # It is necessary to check for None here b/c unblock the queue get by adding
                    # None when we want to stop the service
                    self.writer.send_message(message)

            except ValueError as error:
                # Stream is closed, break out of the loop
                self._log_exception(error, self.OUTPUT_THREAD_NAME)
                break
            except Exception as error:
                # Catch generic exceptions without breaking out of loop
                self._log_exception(error, self.OUTPUT_THREAD_NAME)

    def _dispatch_message(self, message):
        """
        Dispatches a message that was received to the necessary handler
        :param message: The message that was received
        """
        if message.message_type in [JSONRPCMessageType.ResponseSuccess, JSONRPCMessageType.ResponseError]:
            # Responses need to be routed to the handler that requested them
            # TODO: Route to the handler or send error message
            return

        # Figure out which handler will execute the request/notification
        # TODO: Add support for routing of responses
        if message.message_type is JSONRPCMessageType.Request:
            if self._logger is not None:
                self._logger.info(u"Received request id={} method={}".format(
                    message.message_id, message.message_method
                ))
            handler = self._request_handlers[message.message_method]

            # Make sure we got a handler for the request
            if handler is None:
                # TODO: Send back an error message that the request method is not supported
                if self._logger is not None:
                    self._logger.warn(u"Requested method is unsupported {}".format(message.message_method))
                return

            # Call the handler with a request context and the deserialized parameter object
            request_context = RequestContext(message, self._output_queue)
            deserialized_object = handler.class_.from_dict(message.message_params)
            handler.handler(request_context, deserialized_object)
        elif message.message_type is JSONRPCMessageType.Notification:
            if self._logger is not None:
                self._logger.info(u"Received notification method={}".format(message.message_method))
            handler = self._notification_handlers[message.message_method]

            if handler is None:
                # TODO: Send back an error message that the notification method is not supported?
                if self._logger is not None:
                    self._logger.warn(u"Notification method is unsupported".format(message.message_method))
                return

            # Call the handler with a notification context
            notification_context = NotificationContext(self._output_queue)
            deserialized_object = handler.class_()
            deserialized_object.__dict__ = message.message_params
            handler.handler(notification_context, deserialized_object)
        else:
            # If this happens we have a serious issue with the JSON RPC reader
            if self._logger is not None:
                self._logger.warn(u"Received unsupported message type {}".format(message.message_type))
            return

    def _log_exception(self, ex, thread_name):
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        :param thread_name: Name of the thread that encountered the exception
        """
        if self._logger is not None:
            self._logger.warn(u"Thread: {} encountered exception {}".format(thread_name, ex))


class RequestContext:
    """
    Context for a received message
    """

    def __init__(self, message, queue):
        """
        Initializes a new request context
        :param message: The raw request message
        :param queue: Output queue that any outgoing messages will be added to
        """
        self._message = message
        self._queue = queue

    def send_response(self, params):
        """
        Sends a successful response to this request
        :param params: Data to send back with the response
        """
        message = JSONRPCMessage.create_response(self._message.message_id, params)
        self._queue.put(message)

    def send_notification(self, method, params):
        """
        Sends a notification, independent to this request
        :param method: String name of the method for the notification
        :param params: Data to send with the notification
        """
        message = JSONRPCMessage.create_notification(method, params)
        self._queue.put(message)

    def send_error(self, message, data=None, code=0):
        """
        Sends a failure response to this request
        :param message: Concise 1-sentence message explanation of the error
        :param data: Optional data to send back with the error
        :param code: Optional error code to identify the error
        """
        message = JSONRPCMessage.create_error(self._message.message_id, code, message, data)
        self._queue.put(message)


class NotificationContext:
    """
    Context for a received notification
    """

    def __init__(self, queue):
        """
        Initializes a new notification context
        :param queue: Output queue that any outgoing messages will be added to
        """
        self._queue = queue

    def send_notification(self, method, params):
        """
        Sends a new notification over the JSON RPC channel
        :param method: String name of the method of the notification being send
        :param params: Any data to send along with the notification
        """
        message = JSONRPCMessage.create_notification(method, params)
        self._queue.put(message)
