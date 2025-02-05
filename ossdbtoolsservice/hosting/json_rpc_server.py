# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from configparser import ConfigParser
from logging import Logger
from gevent import monkey
from queue import Queue
import threading
import uuid
import json
import ssl
import os

from flask import Flask, request, session, jsonify, make_response
from flask_socketio import SocketIO, disconnect
from flask_cors import CORS
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.json_reader import JSONRPCReader
from ossdbtoolsservice.hosting.json_writer import JSONRPCWriter
from ossdbtoolsservice.utils.path import path_relative_to_base

# Dictionary to store session IDs by WebSocket sid
active_sessions = {}


class JSONRPCServer:
    """
    Handles async requests, async notifications, and async responses
    Supports both HTTP and WebSocket connections when WebServer is enabled
    """
    # CONSTANTS ############################################################
    OUTPUT_THREAD_NAME = u"JSON_RPC_Output_Thread"
    INPUT_THREAD_NAME = u"JSON_RPC_Input_Thread"

    class Handler:
        def __init__(self, class_, handler):
            self.class_ = class_
            self.handler = handler

    def __init__(self,
                 in_stream=None,
                 out_stream=None,
                 logger: Logger = None,
                 enable_web_server=False,
                 listen_address='0.0.0.0',
                 listen_port=8443,
                 disable_keep_alive=False,
                 debug_web_server=False,
                 enable_dynamic_cors=False,
                 config: ConfigParser = None,
                 version='1'):
        """
        Initializes internal state of the server and sets up a few useful built-in request handlers.
        :param in_stream: Input stream that will provide messages from the client. Used when the web server is disabled.
        :param out_stream: Output stream that will send messages to the client. Used when the web server is disabled.
        :param logger: Optional logger for logging purposes.
        :param enable_web_server: Flag to enable or disable the web server. Defaults to False.
        :param listen_address: Address on which the web server will listen. Defaults to '0.0.0.0'.
        :param listen_port: Port on which the web server will listen. Defaults to 8443.
        :param disable_keep_alive: Flag to enable or disable keep-alive for the web server. Defaults to False.
        :param debug_web_server: Flag to enable or disable debug mode for the web server. Defaults to False.
        :param enable_dynamic_cors: Flag to enable or disable dynamic CORS handling. Defaults to False.
        :param config: Configuration object for the server. Defaults to None.
        :param version: Protocol version. Defaults to '1'.
        """
        self._enable_web_server = enable_web_server

        # Enable the web server if the flag is set
        if self._enable_web_server:
            # Patch sockets to make the standard library cooperative https://www.gevent.org/api/gevent.monkey.html
            monkey.patch_all()

            self._listen_address = listen_address
            self._listen_port = listen_port
            self._disable_keep_alive = disable_keep_alive
            self._debug_web_server = debug_web_server
            self._enable_dynamic_cors = enable_dynamic_cors

            # Load the allowed CORS origins from the config file (if available), environment (if available), or use the default value
            cors_origins_config = 'http://localhost'
            if config is not None:
                cors_origins_config = config.get('server', 'cors_origins', fallback='http://localhost')
            cors_origins_env = os.getenv('CORS_ORIGINS', cors_origins_config)
            self._allowed_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]

            self.app = Flask(__name__)
            CORS(self.app, supports_credentials=True, origins=self._allowed_origins)  # Enable CORS
            if self._enable_dynamic_cors:
                self.app.add_url_rule("/<path:dummy>", self._global_options_handler, methods=["OPTIONS"])
                self.app.after_request(self._after_request_handler)
            self.app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Configure session cookie to allow cross-origin requests
            self.app.config["SESSION_COOKIE_SECURE"] = True  # Required for SameSite=None in modern browsers
            self.app.config['SECRET_KEY'] = 'supersecretkey'
            self.app.add_url_rule('/start-session', 'start-session', self._handle_start_session, methods=['POST'])
            self.app.add_url_rule('/json-rpc', 'json_rpc', self._handle_http_request, methods=['POST'])
            ping_interval = 1e9 if self._disable_keep_alive else 25
            self.socketio = SocketIO(self.app, async_mode='gevent', cors_allowed_origins=lambda origin: self._dynamic_cors_handler(
                origin), manage_session=True, logger=logger, engineio_logger=logger, ping_interval=ping_interval, always_connect=False)
            self.socketio.on_event('connect', self._handle_ws_connect)
            self.socketio.on_event('disconnect', self._handle_ws_disconnect)
            self.socketio.on_event('message', self._handle_ws_request)

            # Construct the path to the certificates
            certfile_path = path_relative_to_base('ssl', 'cert.pem')
            keyfile_path = path_relative_to_base('ssl', 'key.pem')

            # Create an SSLContext object
            self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self._ssl_context.load_cert_chain(certfile=certfile_path, keyfile=keyfile_path)

            # Disable stdin reader and stdout writer when web server is disabled.
            self.reader = None
            self.writer = None
            self._output_queue = None
        else:
            # Enable stdin reader and stdout writer only when web server is disabled.
            self.reader = JSONRPCReader(in_stream, logger=logger)
            self.writer = JSONRPCWriter(out_stream, logger=logger)
            self._output_queue = Queue()

            # Disable Flask app and SocketIO when web server is disabled.
            self.app = None
            self.socketio = None

        self._logger = logger
        self._version = version
        self._stop_requested = False

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
        When web server is disabled starts the background threads to listen for responses and requests from
        the underlying streams. Encapsulated into its own method for future async extensions without threads.
        In web server mode, starts the Flask server with SocketIO websocket support.
        """
        self._log_information("JSON RPC server starting...")

        if self._enable_web_server:
            # Start a background task to log the startup message
            self.socketio.start_background_task(self.webserver_started)
            # Start the Flask server with SocketIO websocket support.
            self.socketio.run(self.app, host=self._listen_address, port=self._listen_port, ssl_context=self._ssl_context, debug=self._debug_web_server)
        else:
            # Enable stdout writer only when webserver is disabled.
            self._output_consumer = threading.Thread(
                target=self._consume_output,
                name=self.OUTPUT_THREAD_NAME
            )
            self._output_consumer.daemon = True
            self._output_consumer.start()

            # Enable stdin reader only when webserver is disabled.
            self._input_consumer = threading.Thread(
                target=self._consume_input,
                name=self.INPUT_THREAD_NAME
            )
            self._input_consumer.daemon = True
            self._input_consumer.start()
            message = "JSON RPC server started with input and output stream processing."
            self._log_information(message)
            print(message)

    def stop(self):
        """
        When web server is disabled signals input and output threads to halt asap
        In web server mode, disconnects all clients and stops the server
        """
        self._stop_requested = True
        self._log_information('JSON RPC server stopping...')

        if self._enable_web_server:
            # Disconnect all clients and stop the server
            for sid in active_sessions.values():
                disconnect(sid)
            self.socketio.stop()
        else:
            # Enqueue None to optimistically unblock output thread so it can check for the cancellation flag
            self._output_queue.put(None)

    def webserver_started(self):
        """
        Logs a message when the server has started
        """
        message = f"Web server started on {self._listen_address}:{self._listen_port}"
        self._log_information(message)
        print(message)

    def send_request(self, method, params):
        """
        Add a new request to the output queue
        In web server mode, broadcasts the request to all connected clients over WebSocket
        :param method: Method string of the request
        :param params: Data to send along with the request
        """
        message_id = str(uuid.uuid4())

        # Create the message
        message = JSONRPCMessage.create_request(message_id, method, params)

        if self._enable_web_server:
            # Generate the message string and header string
            json_content = json.dumps(message.dictionary, sort_keys=True)
            self.socketio.send('request', json_content)
        else:
            # TODO: Add support for handlers for the responses
            # Add the message to the output queue
            self._output_queue.put(message)

    def send_notification(self, method, params):
        """
        Sends a notification, independent of any request
        In web server mode, broadcasts the notification to all connected clients over WebSocket
        :param method: String name of the method for the notification
        :param params: Data to send with the notification
        """
        # Create the message
        message = JSONRPCMessage.create_notification(method, params)

        if self._enable_web_server:
            # Generate the message string and header string
            json_content = json.dumps(message.dictionary, sort_keys=True)
            self.socketio.send('notification', json_content)
        else:
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
        This method is a no-op when the web server is enabled.
        """
        # Only wait for IO threads if the webserver is disabled.
        if not self._enable_web_server:
            self._input_consumer.join()
            self._output_consumer.join()
            self._log_information('Input and output threads have completed')

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
        self._log_information('Received shutdown request')
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
        self._log_information('Input thread started')

        while not self._stop_requested:
            try:
                message = self.reader.read_message()
                self._dispatch_message(message)

            except EOFError as error:
                # Thread fails once we read EOF. Halt the input thread
                self._log_thread_exception(error, self.INPUT_THREAD_NAME)
                self.stop()
                break
            except (LookupError, ValueError) as error:
                # LookupError: Content-Length header was not found
                # ValueError: JSON deserialization failed
                self._log_thread_exception(error, self.INPUT_THREAD_NAME)
                # Do not halt the input thread
            except Exception as error:
                # Catch generic exceptions
                self._log_thread_exception(error, self.INPUT_THREAD_NAME)
                # Do not halt the input thread

    def _handle_start_session(self):
        """
        Initiates a connection to the JRPC server over HTTP and starts a session, the value of which will
        be stored in a cookie as session_id. This session_id is used to coorelate future requests, as well
        as associate this client connection with a cooresponding WebSocket connection for asynchronous responses.
        """
        # Create a unique session_id and store it in Flask's session
        session_id = self._ensure_session_id()
        self._log_information(f"Session started with ID: {session_id}")
        return {"session_id": session_id}, 200

    def _handle_http_request(self):
        """
        Handles an incoming HTTP request by processing the JSON-RPC payload and dispatching the message.
        Leverages Flask's session to store the session_id and WebSocket sid which are later used to coorelate
        asynchronous responses and notifications to this request.
        Returns:
            Response: A Flask response object containing the JSON-RPC response or error message.
        """
        # Retrieve the session_id from Flask's session
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({"error": "No session ID found. Please authenticate first."}), 403

        # Look up the WebSocket sid using the session_id
        sid = active_sessions.get(session_id)
        if not sid:
            return jsonify({"error": "No active WebSocket connection found for this session"}), 404

        self._log_information(f"HTTP request was triggered with session_id: {session_id} sid: {sid}")

        # Decode the JSON-RPC message and dispatch it.
        try:
            message = JSONRPCMessage.from_dictionary(request.get_json())
            self._dispatch_message(message, session_id)
            return jsonify({"result": "ok"}), 200
        except Exception as e:
            # Response has invalid json object
            self._log_warning('JSON RPC reader on _handle_http_request() encountered exception: {}'.format(e))
            return jsonify({"error": str(e)}), 500

    def _handle_ws_connect(self):
        """
        Handles an incoming WebSocket connection event by looking up the session_id in Flask's session to
        ensure the client is authenticated and has started a valid session. If authenticated, the WebSocket sid is
        stored in a dictionary with session_id as the key. This ensures a 1:1 mapping between HTTP session and WebSocket
        connection, which is later used to coorelate asynchronous WebSocket responses and notifications to incoming
        HTTP requests.
        Returns:
            Response: True if the WebSocket connection was established and False if it was rejected.
        """
        self._log_information(f"WebSocket connect event triggered with sid: {request.sid}")
        # Map session_id to the WebSocket connection (request.sid)
        session_id = session.get('session_id')
        if session_id:
            active_sessions[session_id] = request.sid
            self._log_information(f"Client connected with session ID: {session_id}")
            return True
        else:
            self._log_warning("Session ID not found for client; disconnecting.")
            # Force the underlying websocket (engineio) to disconnect as socketio.disconnect() relies on the client to respect the disconnect request.
            eio_sid = self._get_eio_sid(request.sid, request.namespace)
            timer = threading.Timer(1.0, self._force_disconnect, args=(eio_sid,))  # Schedule _force_disconnect to run after a 5-second delay with arguments
            timer.start()
            return False

    def _handle_ws_disconnect(self):
        """
        Handles a WebSocket disconnect event by looking up the session_id in the active_sessions dictionary and
        removing the entry if found. This ensures that the session_id is no longer associated with any WebSocket.
        Implements a force disconnect mechanism to ensure the client is disconnected even if they do not respect the
        disconnect request.
        """
        self._log_information(f"WebSocket disconnect event triggered with sid: {request.sid}")
        # Retrieve and remove the session associated with the WebSocket connection
        session_id = None
        for s_id, sid in active_sessions.items():
            if sid == request.sid:
                session_id = s_id
                break

        # Remove the session entry if found
        if session_id:
            del active_sessions[session_id]
            self._log_information(f"Client disconnected with session ID: {session_id}")
            # Perform any additional cleanup based on the session_id if needed
        else:
            self._log_warning("No session found for disconnected client.")

        # Force the underlying websocket (engineio) to disconnect as socketio.disconnect() relies on the client to respect the disconnect request.
        eio_sid = self._get_eio_sid(request.sid, request.namespace)
        self._force_disconnect(eio_sid)

    def _handle_ws_request(self, raw_message):
        self._log_information(f"WebSocket message event triggered with sid: {request.sid}")

        # Retrieve the session_id from Flask's session
        session_id = session.get('session_id')
        if not session_id:
            self.socketio.emit('error', {'result': 'No session ID found. Please authenticate first.'})
            return

        # Look up the WebSocket sid using the session_id
        sid = active_sessions.get(session_id)
        if not sid:
            self.socketio.emit('error', {'result': 'This WebSocket connection does not match an active session.'})
            return

        # Decode the JSON-RPC message and dispatch it.
        try:
            message = JSONRPCMessage.from_dictionary(raw_message)
            self._dispatch_message(message, session_id)
            self.socketio.emit('response', {'result': 'Request accepted!', 'message_id': message.message_id})
        except Exception as e:
            # Response has invalid json object
            self._log_warning('JSON RPC reader on _handle_ws_request() encountered exception: {}'.format(e))
            self.socketio.emit('error', {'result': 'Error processing request!', 'exception': str(e)})

    def _consume_output(self):
        """
        Send output over the output stream
        """
        self._log_information('Output thread started')

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
                self._log_thread_exception(error, self.OUTPUT_THREAD_NAME)
                break
            except Exception as error:
                # Catch generic exceptions without breaking out of loop
                self._log_thread_exception(error, self.OUTPUT_THREAD_NAME)

    def _dispatch_message(self, message, session_id=None):
        """
        Dispatches a message that was received to the necessary handler
        :param message: The message that was received
        :param session_id: The session ID of the client that sent the message, used in web server mode.
        """
        if message.message_type in [JSONRPCMessageType.ResponseSuccess, JSONRPCMessageType.ResponseError]:
            # Responses need to be routed to the handler that requested them
            # TODO: Route to the handler or send error message
            return

        # Figure out which handler will execute the request/notification
        if message.message_type is JSONRPCMessageType.Request:
            self._log_information(f'Received request id={message.message_id} method={message.message_method}')
            handler = self._request_handlers.get(message.message_method)
            request_context = RequestContext(message, self._output_queue, self.socketio, session_id)

            # Make sure we got a handler for the request
            if handler is None:
                # TODO: Localize?
                message = f'Requested method is unsupported: {message.message_method}'
                request_context.send_error(message)
                self._log_warning(message)
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
                self._log_exception(error_message)
                request_context.send_error(error_message, code=-32603)
        elif message.message_type is JSONRPCMessageType.Notification:
            self._log_information(f'Received notification method={message.message_method}')
            handler = self._notification_handlers.get(message.message_method)

            if handler is None:
                # Ignore the notification
                self._log_warning(f'Notification method {message.message_method} is unsupported')
                return

            # Call the handler with a notification context
            notification_context = NotificationContext(self._output_queue, self.socketio, session_id)
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
                self._log_exception(error_message)
        else:
            # If this happens we have a serious issue with the JSON RPC reader
            self._log_warning(f'Received unsupported message type {message.message_type}')
            return

    def _ensure_session_id(self):
        """
        Utility function to ensure session_id exists in the session.
        :return: The session_id
        """
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']

    def _force_disconnect(self, eio_sid):
        """
        Force disconnects a WebSocket client using its engineio session ID.
        Higher-level SocketIO.disconnect() relies on the client to respect the disconnect request, which is not always the case.
        :param eio_sid: The engineio session ID of the client to disconnect
        """
        self._log_information(f"Force disconnecting WebSocket with engineio session ID: {eio_sid}")
        if eio_sid:
            self.socketio.server.eio.disconnect(eio_sid)  # Disconnect the client using its eio session ID

    def _dynamic_cors_handler(self, origin):
        """Determine if the origin is allowed."""
        if self._enable_dynamic_cors:
            return True
        elif origin in self._allowed_origins:
            return True
        return False

    def _global_options_handler(self, dummy):
        """ Handles OPTIONS requests for all routes """
        response = make_response("")
        origin = request.headers.get("Origin", "*")
        self._set_cors_headers(response, origin)
        return response

    def _after_request_handler(self, response):
        """ Handles CORS headers for all HTTP responses """
        # Dynamically set CORS headers
        origin = request.headers.get("Origin", "*")
        self._set_cors_headers(response, origin)
        return response

    def _set_cors_headers(self, response, origin):
        """ Sets the CORS headers on the response """
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    def _get_eio_sid(self, sid, namespace):
        """
        Retrieves the engineio session ID from the WebSocket (SocketIO) session ID and namespace.
        :param sid: The WebSocket session ID from SocketIO
        :param namespace: The namespace of the WebSocket connection
        """
        return self.socketio.server.manager.eio_sid_from_sid(sid, namespace)

    def _log_thread_exception(self, ex, thread_name):
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        :param thread_name: Name of the thread that encountered the exception
        """
        if self._logger is not None:
            self._logger.exception('Thread %s encountered exception %s', thread_name, ex)

    def _log_exception(self, message):
        """
        Logs an exception if the logger is defined
        :param message: Exception to log
        """
        if self._logger is not None:
            self._logger.exception(message)

    def _log_information(self, message):
        """
        Logs information if the logger is defined
        :param message: Information to log
        """
        if self._logger is not None:
            self._logger.info(message)

    def _log_warning(self, message):
        """
        Logs a warning if the logger is defined
        :param message: Warning to log
        """
        if self._logger is not None:
            self._logger.warn(message)


class OutgoingMessageRegistration:
    """Object that stores the info for registering a response or notification"""

    # Static collection to store all outgoing message configurations
    message_configurations = []

    @staticmethod
    def register_outgoing_message(message_class):
        """
        Registers an outgoing message configuration
        :param message_class: Class to deserialize the response parameters into
        """
        OutgoingMessageRegistration.message_configurations.append(message_class)


class IncomingMessageConfiguration:
    """Object that stores the info for registering a request"""

    # Static collection to store all incoming message configurations
    message_configurations = []

    def __init__(self, method, parameter_class):
        """
        Constructor for request configuration
        :param method: String name of the method to respond to
        :param parameter_class: Class to deserialize the request parameters into
        """
        self.method = method
        self.parameter_class = parameter_class
        IncomingMessageConfiguration.message_configurations.append(self)


class RequestContext:
    """
    Context for a received message
    """

    def __init__(self, message, queue, socketio=None, session_id=None):
        """
        Initializes a new request context
        :param message: The raw request message
        :param queue: Output queue that any outgoing messages will be added to
        :param socketio: The SocketIO instance to use for sending messages over WebSocket
        :param session_id: The session ID of the client that sent the request
        """
        self._message = message
        self._queue = queue
        self._socketio = socketio
        self._session_id = session_id

    def send_response(self, params):
        """
        Sends a successful response to this request
        :param params: Data to send back with the response
        """
        message = JSONRPCMessage.create_response(self._message.message_id, params)
        if self._socketio and self._session_id:
            self._send_over_socket('response', message)
        else:
            self._queue.put(message)

    def send_notification(self, method, params):
        """
        Sends a notification, independent to this request
        :param method: String name of the method for the notification
        :param params: Data to send with the notification
        """
        message = JSONRPCMessage.create_notification(method, params)
        if self._socketio and self._session_id:
            self._send_over_socket('notification', message)
        else:
            self._queue.put(message)

    def send_error(self, message, data=None, code=0):
        """
        Sends a failure response to this request
        :param message: Concise 1-sentence message explanation of the error
        :param data: Optional data to send back with the error
        :param code: Optional error code to identify the error
        """
        message = JSONRPCMessage.create_error(self._message.message_id, code, message, data)
        if self._socketio and self._session_id:
            self._send_over_socket('error', message)
        else:
            self._queue.put(message)

    def send_unhandled_error_response(self, ex: Exception):
        """Send response for any unhandled exceptions"""
        self.send_error('Unhandled exception: {}'.format(str(ex)))  # TODO: Localize

    def _send_over_socket(self, event, message):
        """
        Sends a message over the WebSocket to the client that made the initial request
        :param event: The socket event to send, e.g. 'response', 'notification', 'error'
        :param message: The message to send
        """
        if self._socketio and self._session_id:
            # Generate the message string and header string
            json_content = json.dumps(message.dictionary, sort_keys=True)

            # Send the message back via WebSocket if the client is still connected
            sid = active_sessions.get(self._session_id)
            if sid:
                self._socketio.emit(event, json_content, to=sid)


class NotificationContext:
    """
    Context for a received notification
    """

    def __init__(self, queue, socketio=None, session_id=None):
        """
        Initializes a new notification context
        :param queue: Output queue that any outgoing messages will be added to
        :param socketio: The SocketIO instance to use for sending messages over WebSocket
        :param session_id: The session ID of the client that sent the request
        """
        self._queue = queue
        self._socketio = socketio
        self._session_id = session_id

    def send_notification(self, method, params):
        """
        Sends a new notification over the JSON RPC channel
        :param method: String name of the method of the notification being send
        :param params: Any data to send along with the notification
        """
        message = JSONRPCMessage.create_notification(method, params)
        if self._socketio and self._session_id:
            # Generate the message string and header string
            json_content = json.dumps(message.dictionary, sort_keys=True)

            # Send the message back via WebSocket if the client is still connected
            sid = active_sessions.get(self._session_id)
            if sid:
                self._socketio.emit('notification', json_content, to=sid)
        else:
            self._queue.put(message)
