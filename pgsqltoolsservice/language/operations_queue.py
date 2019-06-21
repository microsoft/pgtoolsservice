# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles queueing """
from typing import Callable, Dict, List, Optional   # noqa
import threading
from queue import Queue

from pgsmo.utils.querying import DriverManager, ServerConnection
from pgsqltoolsservice.hosting import ServiceProvider

from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectRequestParams, ConnectionType
from pgsqltoolsservice.language.completion import PGCompleter
from pgsqltoolsservice.language.completion_refresher import CompletionRefresher
import pgsqltoolsservice.utils as utils

INTELLISENSE_URI = 'intellisense://'


class ConnectionContext:
    """Context information needed to look up connections"""

    def __init__(self, key: str):
        self.key = key
        self.intellisense_complete: threading.Event = threading.Event()
        self.pgcompleter: PGCompleter = None
        self.is_connected: bool = False

    def refresh_metadata(self, connection: ServerConnection):
        # Start metadata refresh so operations can be completed
        completion_refresher = CompletionRefresher(connection)
        completion_refresher.refresh(self._on_completions_refreshed)

    # IMPLEMENTATION DETAILS ###############################################
    def _on_completions_refreshed(self, new_completer: PGCompleter):
        self.pgcompleter = new_completer
        self.is_connected = True
        self.intellisense_complete.set()


class QueuedOperation:
    """Information about an operation to be queued"""

    def __init__(self, key: str, task: Callable[[PGCompleter], bool], timeout_task: Callable[[None], bool]):
        """
        Initializes a queued operation with a key defining the connection it maps to,
        a task to be run for a connected queue, and a timeout task. Currently the timeout
        task is just used if the queue is not yet connected
        """
        self.key = key
        self.task: Callable[[PGCompleter], bool] = task
        self.timeout_task: Callable[[None], bool] = timeout_task
        self.context: ConnectionContext = None


class OperationsQueue:
    """
    Handles requests to queue operations that require a connection. Currently this works
    by having a single queue per connection.
    """
    # CONSTANTS ############################################################
    OPERATIONS_THREAD_NAME = u"LANG_SVC_Operations"

    def __init__(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self.lock: threading.RLock = threading.RLock()
        self.queue: Queue = Queue()
        self._context_map: Dict[str, ConnectionContext] = {}
        self.stop_requested = False
        # TODO consider thread pool for multiple messages? Or full
        # Process queue using multi-threading
        self._operations_consumer: threading.Thread = None

    # PUBLIC METHODS ###############################################
    def start(self):
        """
        Starts the thread that processes operations
        """
        self._log_info('Language Service Operations Queue starting...')
        self._operations_consumer = threading.Thread(
            target=self._process_operations,
            args=(),
            name=self.OPERATIONS_THREAD_NAME
        )
        self._operations_consumer.daemon = True
        self._operations_consumer.start()

    def stop(self):
        self.stop_requested = True
        # Enqueue None to optimistically unblock output thread so it can check for the cancellation flag
        self.queue.put(None)
        self._log_info('Language Service Operations Queue stopping...')

    def add_operation(self, operation: QueuedOperation):
        """
        Adds an operation to the correct queue. Raises KeyError if no queue exists for this connection
        """
        if not operation:
            # Must throw in this case, as a None operation is used to close the
            # queue
            raise ValueError('Operation must not be None')
        with self.lock:
            # Get the connection context or throw KeyError if not found
            context: ConnectionContext = self._context_map[operation.key]
            operation.context = context
            self.queue.put(operation)

    def has_connection_context(self, conn_info: ConnectionInfo) -> bool:
        """
        Checks if there's a connection context for a given connection in the map.
        Intentional does not lock as this is intended for quick lookup
        """
        key: str = OperationsQueue.create_key(conn_info)
        return key in self._context_map

    def add_connection_context(self, conn_info: ConnectionInfo, overwrite=False) -> ConnectionContext:
        """
        Adds a connection context and returns the notification event.
        If a connection queue exists alread, will overwrite if necesary
        """
        with self.lock:
            key: str = OperationsQueue.create_key(conn_info)
            context: ConnectionContext = self._context_map.get(key)
            if context:
                if overwrite:
                    self.disconnect(key)
                else:
                    # Notify ready and return immediately, the queue exists
                    return context
            # Create the context and start refresh
            context = ConnectionContext(key)
            conn = self._create_connection(key, conn_info)
            context.refresh_metadata(conn)
            self._context_map[key] = context
            return context

    def disconnect(self, connection_key: str):
        """
        Disconnects a connection that was used for intellisense
        """
        with self.lock:
            # Pop the key from the queue as it's no longer needed
            context: ConnectionContext = self._context_map.pop(connection_key, None)
            if context:
                key_uri = INTELLISENSE_URI + connection_key
                try:
                    self._connection_service.disconnect(key_uri, ConnectionType.INTELLISENSE)
                except Exception as ex:
                    self._log_exception('error during disconnect, ignoring as assume already disconnected: {0}'.format(ex))

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def create_key(cls, conn_info: ConnectionInfo) -> str:
        """
        Creates a key uniquely identifying a ConnectionInfo object for use in caching
        """
        return '{0}|{1}|{2}'.format(conn_info.details.server_name, conn_info.details.database_name, conn_info.details.user_name)

    def _create_connection(self, connection_key: str, conn_info: ConnectionInfo) -> Optional[ServerConnection]:
        conn_service = self._connection_service
        key_uri = INTELLISENSE_URI + connection_key
        connect_request = ConnectRequestParams(conn_info.details, key_uri, ConnectionType.INTELLISENSE)
        connect_result = conn_service.connect(connect_request)
        if connect_result.error_message is not None:
            raise RuntimeError(connect_result.error_message)

        connection = conn_service.get_connection(key_uri, ConnectionType.INTELLISENSE)
        return connection

    def _process_operations(self):
        """
        Threaded operation that runs to process the queue.
        Thread completes on cancelation
        """
        while not self.stop_requested:
            try:
                # Block until queue contains a message to send
                operation: QueuedOperation = self.queue.get()
                self.execute_operation(operation)
            except ValueError as error:
                # Stream is closed, break out of the loop
                self._log_thread_exception(error)
                break
            except Exception as error:
                # Catch generic exceptions without breaking out of loop
                self._log_thread_exception(error)

    def execute_operation(self, operation: QueuedOperation):
        """
        Processes an operation. Seperated for test purposes from the threaded logic
        """
        if operation is not None:
            # Try to process the task, falling back to the timeout
            # task if disconnected or regular task failed
            is_connected = operation.context is not None and operation.context.is_connected
            run_timeout_task = not is_connected
            if is_connected:
                run_timeout_task = not operation.task(operation.context)
            if run_timeout_task:
                operation.timeout_task()

    @property
    def _connection_service(self) -> ConnectionService:
        return self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]

    def _log_exception(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.exception(message)

    def _log_info(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.info(message)

    def _log_thread_exception(self, ex):
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        """
        self._log_exception('Thread {0} encountered exception {1}'.format(threading.currentThread(), ex))
