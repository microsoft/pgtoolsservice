from queue import Queue

import enum
import json
import threading
import uuid


class JsonRpcServer:
    """
    Handles async requests, async notifications, and async responses
    """
    # CONSTANTS ############################################################
    OUTPUT_THREAD_NAME = u"JSON_RPC_Output_Thread"
    INPUT_THREAD_NAME = u"JSON_RPC_Input_Thread"

    def __init__(self, in_stream, out_stream, logger=None):
        self.writer = JsonRpcWriter(out_stream)
        self.reader = JsonRpcReader(in_stream)
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
        self._output_consumer.start()

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

    def submit_request(self, method, params):
        """
        Add a new request to the output queue
        :param method: Method string of the request
        :param params: Data to send along with the request
        """
        message_id = str(uuid.uuid4())

        # Create the message
        message = JsonRpcMessage.create_request(message_id, method, params)

        # TODO: Add support for handlers for the responses
        # Add the message to the output queue
        self._output_queue.put(message)

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
                if message.message_type in [JsonRpcMessageType.ResponseSuccess, JsonRpcMessageType.ResponseError]:
                    # Responses need to be routed to the handler that requested them
                    # TODO: Route to the handler or send error message
                    continue

                # Figure out which handler will execute the request/notification
                if message.message_type is JsonRpcMessageType.Request:
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
                        continue

                    # Call the handler with a request context
                    # TODO: Deserialize the json
                    request_context = RequestContext(message, self.writer)
                    handler(request_context, message.message_params)
                elif message.message_type is JsonRpcMessageType.Notification:
                    if self._logger is not None:
                        self._logger.info(u"Received notification method={}".format(message.message_method))
                    handler = self._notification_handlers[message.message_method]

                    if handler is None:
                        # TODO: Send back an error message that the notification method is not supported?
                        if self._logger is not None:
                            self._logger.warn(u"Notification method is unsupported".format(message.message_method))
                        continue

                    # Call the handler with a notification context
                    # TODO: Deserialize the json
                    notification_context = NotificationContext(self.writer)
                    handler(notification_context, message.message_params)
                else:
                    # If this happens we have a serious issue with the JSON RPC reader
                    if self._logger is not None:
                        self._logger.warn(u"Received unsupported message type {}".format(message.message_type))
                    continue

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

    def _log_exception(self, ex, thread_name):
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        :param thread_name: Name of the thread that encountered the exception
        """
        if self._logger is not None:
            self._logger.warn(u"Thread: {} encountered exception {}".format(thread_name, ex))


class JsonRpcWriter:
    """
    Write JSON RPC messages to a stream
    """

    HEADER = u"Content-Length: {}\r\n\r\n"

    def __init__(self, stream, encoding=None, logger=None):
        """
        Initializes the JSON RPC writer
        :param stream: Stream that messages will be sent on
        :param encoding: Optional encoding choice for messages. Defaults to UTF-8
        :param logger: Optional destination for logging
        """
        self.stream = stream
        self.encoding = encoding or u'UTF-8'
        self._logger = logger

    # METHODS ##############################################################
    def close(self):
        """
        Closes the stream
        """
        try:
            self.stream.close()
        except AttributeError:
            pass

    def send_message(self, message):
        """
        Sends JSON RPC message as defined by message object
        :param message: Message to send
        """
        # Generate the message string and header string
        json_content = json.dumps(message.dictionary(), sort_keys=True)
        header = self.HEADER.format(str(len(json_content)))

        # Write the message to the stream
        self.stream.write(header.encode(u"ascii"))
        self.stream.write(json_content.encode(self.encoding))
        self.stream.flush()

        if self._logger is not None:
            self._logger.info("{} message sent id={} method={}".format(
                message.message_type.name,
                message.message_id,
                message.message_method
            ))


class JsonRpcReader:
    """
    Reads JSON RPC message from a stream
    """

    # CONSTANTS ############################################################
    CR = 13
    LF = 10
    BUFFER_RESIZE_TRIGGER = 0.25
    DEFAULT_BUFFER_SIZE = 8192

    class ReadState(enum.Enum):
        Header = 1,
        Content = 2

    # CONSTRUCTOR ##########################################################
    def __init__(self, stream, encoding=None, logger=None):
        """
        Initializes the JSON RPC reader
        :param stream: Stream that messages will be read from
        :param encoding: Optional encoding choice for messages. Defaults to UTF-8
        :param logger: Optional destination for logging
        """
        self.stream = stream
        self.encoding = encoding or u'UTF-8'
        self._logger = logger

        self._buffer = bytearray(self.DEFAULT_BUFFER_SIZE)
        # Pointer to end of buffer content
        self._buffer_end_offset = 0
        # Pointer to where we have read up to
        self._read_offset = 0

        # Setup message reading state
        self._expected_content_length = 0
        self._headers = {}
        self._read_state = self.ReadState.Header
        self._needs_more_data = True

    # METHODS ##############################################################
    def close(self):
        """
        Close the stream
        """
        try:
            self.stream.close()
        except AttributeError:
            pass

    def read_message(self):
        """
        Read JSON RPC message from buffer
        :raises ValueError: if the body-content cannot be serialized to a JSON object
        :return: JsonRpcMessage that was received
        """
        # Using a mutable list to hold the value since an immutable string passed by reference won't
        # change the value
        content = ['']
        try:
            while not self._needs_more_data or self._read_next_chunk():
                # We should have all the data we need to form a message in the buffer. If we need
                # more data to form the next message, this flag will be reset by an attempt to form
                # a header or content
                self._needs_more_data = False

                # If we can't read a header, read the next chunk
                if self._read_state is self.ReadState.Header and not self._try_read_headers():
                    self._needs_more_data = True
                    continue

                # If we read the header, try the content. If that fails, read the next chunk
                if self._read_state is self.ReadState.Content and not self._try_read_content(content):
                    self._needs_more_data = True
                    continue

                # We have the content
                break

            # Resize the buffer and remove bytes we have read
            self._trim_buffer_and_resize(self._read_offset)
            return JsonRpcMessage(json.loads(content[0]))
        except ValueError as ve:
            # Response has invalid json object
            if self._logger is not None:
                self._logger.warn(u"JSON RPC reader on read_response() encountered exception: {}".format(ve))
            raise

    # IMPLEMENTATION DETAILS ###############################################

    def _read_next_chunk(self):
        """
        Read a chunk from the output stream into buffer
        :raises EOFError: Stream was empty or stream did not contain a valid header or content-body
        :raises ValueError: Stream was closed externally
        :return: True on successful read of a message chunk
        """
        # Check if we need to resize the buffer
        current_buffer_size = len(self._buffer)
        if (current_buffer_size - self._buffer_end_offset) / current_buffer_size < self.BUFFER_RESIZE_TRIGGER:
            # Resize the buffer, copy the old contents, and point to the new buffer
            resized_buffer = bytearray(current_buffer_size * 2)
            resized_buffer[0:current_buffer_size] = self._buffer
            self._buffer = resized_buffer

        # Memory view is required in order to read into a subset of a byte array
        try:
            length_read = self.stream.readinto(memoryview(self._buffer)[self._buffer_end_offset])
            self._buffer_end_offset += length_read

            if not length_read:
                if self._logger is not None:
                    self._logger.warn(u"JSON RPC Reader reached end of stream")
                raise EOFError(u"End of stream reached, no output.")

            return True
        except ValueError as ex:
            # Stream was closed
            if self._logger is not None:
                self._logger.warn(u"JSON RPC Reader on read_next_chunk encountered exception: {}".format(ex))
            raise

    def _try_read_headers(self):
        """
        Try to read the header information from the internal bufffer expecting the last header to contain '\r\n\r\n'
        :raises LookupError: The content-length header was not found
        :raises ValueError: The content-length contained an invalid literal for int
        :return: True on successful read of headers, False on failure to find headers
        """
        # Scan the buffer up until right before the \r\n\r\n
        scan_offset = self._read_offset
        while scan_offset + 3 < self._buffer_end_offset and (
            self._buffer[scan_offset] != self.CR or
            self._buffer[scan_offset+1] != self.LF or
            self._buffer[scan_offset+2] != self.CR or
            self._buffer[scan_offset+3] != self.LR
        ):
            scan_offset += 1

        # If we reached the end of the vuffer
            if scan_offset + 3 >= self._buffer_end_offset:
                return False

        # Split the headers by newline
        try:
            headers_read = self._buffer[self._read_offset:scan_offset].decode(u'ascii')
            for header in headers_read.split(u'\n'):
                colon_index = header.find(u':')

                # Make sure there's a colon to split key and value on
                if colon_index == -1:
                    if self._logger is not None:
                        self._logger.warn(u"JSON RPC reader encountered missing colons in try_read_headers()")
                    raise KeyError(u"Colon missing from header: {}".format(header))

                # Case insensitive check
                header_key = header[:colon_index].strip().lower()
                header_value = header[colon_index + 1:].strip()

                # Was content-length found?
                if not 'content-length' in self._headers:
                    if self._logger is not None:
                        self._logger.warn(u"JSON RPC reader did not find Content-Length in the headers")
                    raise LookupError(u"Content-Length was not found in headers received.")

                self._expected_content_length = int(self._headers['content-length'])
        except ValueError:
            # Content-Length contained invalid literal for int
            self._trim_buffer_and_resize(scan_offset + 4)
            raise

        # Pushing read pointer past the newline character
        self._read_offset = scan_offset + 4
        self._read_state = self.ReadState.Content

        return True

    def _try_read_content(self, content):
        """
        Try to read content from internal buffer
        :param content: Location to store the content
        :return: True on successful reading of content, False on incomplete read of content (based on content-length)
        """
        if self._buffer_end_offset - self._read_offset < self._expected_content_length:
            # We buffered less than the expected content length
            return False

        content[0] = self._buffer[self._read_offset:self._read_offset + self._expected_content_length]\
            .decode(self.encoding)
        self._read_offset += self._expected_content_length

        self._read_state = self.ReadState.Header

        return True

    def _trim_buffer_and_resize(self, bytes_to_remove):
        """
        Trim the buffer by the passed in bytes_to_remove by creating a new buffer that is at a minimum the
        default max size
        :param bytes_to_remove: Number of bytes to remove from the current buffer 
        """
        current_buffer_size = len(self._buffer)

        # Create a new buffer with either minimum size of leftover size
        new_buffer = bytearray(max(current_buffer_size - bytes_to_remove, self.DEFAULT_BUFFER_SIZE))

        # If we have content we did not read, copy that portion to the new buffer
        if bytes_to_remove <= current_buffer_size:
            new_buffer[:self._buffer_end_offset - bytes_to_remove] = \
                self._buffer[bytes_to_remove:self._buffer_end_offset]

        # Point to the new buffer
        self._buffer = new_buffer

        # Reset pointers after the shift
        self._read_offset = 0
        self._buffer_end_offset -= bytes_to_remove


class JsonRpcMessageType(enum):
    Request = 1
    ResponseSuccess = 2
    ResponseError = 3
    Notification = 4


class JsonRpcMessage:
    """
    Internal representation of a JSON RPC message. Provides logic for converting back and forth
    from dictionary
    """

    # CONSTRUCTORS #########################################################
    @classmethod
    def create_error(cls, msg_id, code, message, data):
        error = {
            u"code": code,
            u"message": message,
            u"data": data
        }
        return cls(JsonRpcMessageType.ResponseError, msg_id=msg_id, msg_error=error)

    @classmethod
    def create_notification(cls, method, params):
        return cls(JsonRpcMessageType.Notification, msg_method=method, msg_params=params)

    @classmethod
    def create_request(cls, msg_id, method, params):
        return cls(JsonRpcMessageType.Request, msg_id=msg_id, msg_method=method, msg_params=params)

    @classmethod
    def create_response(cls, msg_id, result):
        return cls(JsonRpcMessageType.ResponseSuccess, msg_id=msg_id, msg_result=result)

    @classmethod
    def from_dictionary(cls, msg_dict):
        """
        Decomposes a dictionary from a JSON RPC message into components with light validation
        :param msg_dict: Dictionary of components from deserializing a JSON RPC message
        :return: JsonRpcMessage that is setup as per the dictionary 
        """
        # Read all the possible values in from the message dictionary
        # If the keys don't exist in the dict, then None is set, which is acceptable
        msg_id = msg_dict.get(u"id")
        msg_method = msg_dict.get(u"method")
        msg_params = msg_dict.get(u"params")
        msg_result = msg_dict.get(u"result")
        msg_error = msg_dict.get(u"error")

        if msg_id is None:
            # Messages that lack an id are notifications
            if msg_method is None:
                raise ValueError("Notification message is missing method")
            msg_type = JsonRpcMessageType.Notification

        else:
            # Message has id, therefore it is a response or a request
            if msg_result is not None:
                # A result field indicates this is a successful response
                msg_type = JsonRpcMessageType.ResponseSuccess
            elif msg_error is not None:
                # An error field indicated this is a failure response
                msg_type = JsonRpcMessageType.ResponseError
            else:
                # Lack of a result or error field indicates a request message
                if msg_method is None:
                    raise ValueError("Request message is missing method")
                msg_type = JsonRpcMessageType.Request

        return cls(msg_type, msg_id, msg_method, msg_params, msg_result, msg_error)

    def __init__(self, msg_type,
                 msg_id=None,
                 msg_method=None,
                 msg_params=None,
                 msg_result=None,
                 msg_error=None):
        self._message_type = msg_type
        self._message_id = msg_id
        self._message_method = msg_method
        self._message_params = msg_params
        self._message_result = msg_result
        self._message_error = msg_error

    # PROPERTIES ###########################################################
    @property
    def message_id(self):
        return self._message_id

    @property
    def message_method(self):
        return self._message_method

    @property
    def message_params(self):
        return self._message_params

    @property
    def message_result(self):
        return self._message_result

    @property
    def message_error(self):
        return self._message_error

    @property
    def message_type(self):
        return self._message_type

    @property
    def dictionary(self):
        message_base = {u"jsonrpc": u"2.0"}

        if self._message_type is JsonRpcMessageType.Request:
            message_base[u"method"] = self._message_method
            message_base[u"params"] = self._message_params
            message_base[u"id"] = self._message_id
            return message_base

        if self._message_type is JsonRpcMessageType.ResponseSuccess:
            message_base[u"result"] = self._message_result
            message_base[u"id"] = self._message_id
            return message_base

        if self._message_type is JsonRpcMessageType.Notification:
            message_base[u"method"] = self._message_method
            message_base[u"params"] = self._message_params
            return message_base

        if self._message_type is JsonRpcMessageType.ResponseError:
            message_base[u"error"] = self._message_error
            message_base[u"id"] = self._message_id
            return message_base


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
        message = JsonRpcMessage.create_response(self._message.message_id, params)
        self._queue.put(message)

    def send_notification(self, method, params):
        """
        Sends a notification, independent to this request
        :param method: String name of the method for the notification
        :param params: Data to send with the notification
        """
        message = JsonRpcMessage.create_notification(method, params)
        self._queue.put(message)

    def send_error(self, message, data=None, code=0):
        """
        Sends a failure response to this request
        :param message: Concise 1-sentence message explanation of the error
        :param data: Optional data to send back with the error
        :param code: Optional error code to identify the error
        """
        message = JsonRpcMessage.create_error(self._message.message_id, code, message, data)
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
        message = JsonRpcMessage.create_notification(method, params)
        self._queue.put(message)
