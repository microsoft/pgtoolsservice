# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from queue import Queue
import threading
import uuid

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.json_reader import JSONRPCReader
from ossdbtoolsservice.hosting.json_writer import JSONRPCWriter
from ossdbtoolsservice.exception.OssdbErrorConstants import OssdbErrorConstants


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

    def __init__(self, in_stream, out_stream, logger=None, version='0'):
        """
        Initializes internal state of the server and sets up a few useful built-in request handlers
        :param in_stream: Input stream that will provide messages from the client
        :param out_stream: Output stream that will send message to the client
        :param logger: Optional logger
        :param version: Protocol version. Defaults to 0
        """
        self.writer = JSONRPCWriter(out_stream, logger=logger)
        self.reader = JSONRPCReader(in_stream, logger=logger)
        self._logger = logger
        self._version = version
        self._stop_requested = False

        self._output_queue = Queue()

        self._request_handlers = {}
        self._notification_handlers = {}
        self._shutdown_handlers = []

        self._output_consumer = None
        self._input_consumer = None

        # Register built-in handlers
        # 1) Echo
        echo_config = IncomingMessageConfiguration('echo', None)
        self.set_request_handler(echo_config, self._handle_echo_request)

        # 2) Protocol version
        version_config = IncomingMessageConfiguration('version', None)
        self.set_request_handler(version_config, self._handle_version_request)

        # 3) Shutdown/exit
        shutdown_config = IncomingMessageConfiguration('shutdown', None)
        self.set_request_handler(shutdown_config, self._handle_shutdown_request)
        exit_config = IncomingMessageConfiguration('exit', None)
        self.set_request_handler(exit_config, self._handle_shutdown_request)

    # METHODS ##############################################################

    def add_shutdown_handler(self, handler):
        """
        Adds the provided shutdown handler to the list of shutdown handlers
        :param handler: The callable handler to call when shutdown occurs
        """
        self._shutdown_handlers.append(handler)

    def count_shutdown_handlers(self) -> int:
        """
        Returns the number of shutdown handlers registered
        """
        return len(self._shutdown_handlers)

    def start(self):
        """
        Starts the background threads to listen for responses and requests from the underlying
        streams. Encapsulated into its own method for future async extensions without threads
        """
        if self._logger is not None:
            self._logger.info("JSON RPC server starting...")

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
        Signal input and output threads to halt asap
        """
        self._stop_requested = True

        # Enqueue None to optimistically unblock output thread so it can check for the cancellation flag
        self._output_queue.put(None)

        if self._logger is not None:
            self._logger.info('JSON RPC server stopping...')

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

    def send_notification(self, method, params):
        """
        Sends a notification, independent of any request
        :param method: String name of the method for the notification
        :param params: Data to send with the notification
        """
        # Create the message
        message = JSONRPCMessage.create_notification(method, params)

        # TODO: Add support for handlers for the responses
        # Add the message to the output queue
        self._output_queue.put(message)

    def set_request_handler(self, config, handler):
        """
        Sets the handler for a request with a given configuration
        :param config: Configuration of the request to listen for
        :param handler: Handler to call when the server receives a request that matches the config
        """
        self._request_handlers[config.method] = self.Handler(config.parameter_class, handler)

    def set_notification_handler(self, config, handler):
        """
        Sets the handler for a notification with a given configuration
        :param config: Configuration of the notification to listen for
        :param handler: Handler to call when the server receives a notification that matches the config
        """
        self._notification_handlers[config.method] = self.Handler(config.parameter_class, handler)

    def wait_for_exit(self):
        """
        Blocks until both input and output threads return, ie, until the server stops.
        """
        self._input_consumer.join()
        self._output_consumer.join()
        if self._logger is not None:
            self._logger.info('Input and output threads have completed')

        # Close the reader/writer here instead of in the stop method in order to allow "softer"
        # shutdowns that will read or write the last message before halting
        self.reader.close()
        self.writer.close()

    # BUILT-IN HANDLERS ####################################################

    @staticmethod
    def _handle_echo_request(request_context, params):
        request_context.send_response(params)

    def _handle_version_request(self, request_context, params):
        request_context.send_response(self._version)

    def _handle_shutdown_request(self, request_context, params):
        # Signal that the threads should stop
        if self._logger is not None:
            self._logger.info('Received shutdown request')
        self._stop_requested = True

        # Execute the shutdown request handlers
        for handler in self._shutdown_handlers:
            handler()

        self.stop()

    # IMPLEMENTATION DETAILS ###############################################

    def _consume_input(self):
        """
        Listen for messages from the input stream and dispatch them to the registered listeners
        :raises ValueError: The stream was closed. Exit the thread immediately.
        :raises LookupError: No void header with content-length was found
        :raises EOFError: The stream may not contain any bytes yet, so retry.
        """
        if self._logger is not None:
            self._logger.info('Input thread started')

        while not self._stop_requested:
            try:
                message = self.reader.read_message()
                self._dispatch_message(message)

            except EOFError as error:
                # Thread fails once we read EOF. Halt the input thread
                self._log_exception(error, self.INPUT_THREAD_NAME)
                self.stop()
                break
            except (LookupError, ValueError) as error:
                # LookupError: Content-Length header was not found
                # ValueError: JSON deserialization failed
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
        if self._logger is not None:
            self._logger.info('Output thread started')

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
        if message.message_type is JSONRPCMessageType.Request:
            if self._logger is not None:
                self._logger.info('Received request id=%s method=%s', message.message_id, message.message_method)
            handler = self._request_handlers.get(message.message_method)
            request_context = RequestContext(message, self._output_queue)

            # Make sure we got a handler for the request
            if handler is None:
                # TODO: Localize?
                request_context.send_error(message=f'Requested method is unsupported: {message.message_method}', code=OssdbErrorConstants.UNSUPPORTED_REQUEST_METHOD)
                if self._logger is not None:
                    self._logger.warn('Requested method is unsupported: %s', message.message_method)
                return

            # Call the handler with a request context and the deserialized parameter object
            if handler.class_ is None:
                # Don't attempt to do complex deserialization
                deserialized_object = message.message_params
            else:
                # Use the complex deserializer
                deserialized_object = handler.class_.from_dict(message.message_params)
            try:
                handler.handler(request_context, deserialized_object)
            except Exception as e:
                error_message = f'Unhandled exception while handling request method {message.message_method}: "{e}"'  # TODO: Localize
                if self._logger is not None:
                    self._logger.exception(error_message)
                request_context.send_error(message=error_message, code=OssdbErrorConstants.REQUEST_METHOD_PROCESSING_UNHANDLED_EXCEPTION)
        elif message.message_type is JSONRPCMessageType.Notification:
            if self._logger is not None:
                self._logger.info('Received notification method=%s', message.message_method)
            handler = self._notification_handlers.get(message.message_method)

            if handler is None:
                # Ignore the notification
                if self._logger is not None:
                    self._logger.warn('Notification method %s is unsupported', message.message_method)
                return

            # Call the handler with a notification context
            notification_context = NotificationContext(self._output_queue)
            deserialized_object = None
            if handler.class_ is None:
                # Don't attempt to do complex deserialization
                deserialized_object = message.message_params
            else:
                # Use the complex deserializer
                deserialized_object = handler.class_.from_dict(message.message_params)
            try:
                handler.handler(notification_context, deserialized_object)
            except Exception:
                error_message = f'Unhandled exception while handling notification method {message.message_method}'
                if self._logger is not None:
                    self._logger.exception(error_message)
        else:
            # If this happens we have a serious issue with the JSON RPC reader
            if self._logger is not None:
                self._logger.warn('Received unsupported message type %s', message.message_type)
            return

    def _log_exception(self, ex, thread_name):
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        :param thread_name: Name of the thread that encountered the exception
        """
        if self._logger is not None:
            self._logger.exception('Thread %s encountered exception %s', thread_name, ex)


class IncomingMessageConfiguration:
    """Object that stores the info for registering a request"""

    def __init__(self, method, parameter_class):
        """
        Constructor for request configuration
        :param method: String name of the method to respond to
        :param parameter_class: Class to deserialize the request parameters into
        """
        self.method = method
        self.parameter_class = parameter_class


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

    def send_unhandled_error_response(self, ex: Exception, code=0):
        """Send response for any unhandled exceptions"""
        self.send_error(message='Unhandled exception: {}'.format(str(ex)), code=code)  # TODO: Localize


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
