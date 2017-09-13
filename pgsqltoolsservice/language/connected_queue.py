# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles queueing """
import functools
from typing import Callable, Dict, List, Optional
import threading
from queue import Queue, Empty
import psycopg2

from pgsqltoolsservice.hosting import ServiceProvider
from pgsqltoolsservice.connection import ConnectionInfo, ConnectionService
from pgsqltoolsservice.connection.contracts import ConnectRequestParams, ConnectionDetails, ConnectionType
from pgsqltoolsservice.language.contracts import (
    INTELLISENSE_READY_NOTIFICATION, IntelliSenseReadyParams
)
from pgsqltoolsservice.language.completion import PGCompleter
from pgsqltoolsservice.language.completion_refresher import CompletionRefresher
import pgsqltoolsservice.utils as utils

POLL_TIMEOUT = 1     # wait 1 second before checking cancelation
INTELLISENSE_URI = 'intellisense://'


class ConnectionContext:
    """Context information needed to look up connections"""
    def __init__(self, key: str, intellisense_complete: threading.Event):
        self.key = key
        self.intellisense_complete = intellisense_complete


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


class ConnectedQueue:
    """A Queue for a single connection"""

    def __init__(self, connection_key: str, connection: 'psycopg2.extensions.connection'):
        # Define core params
        self.connection_key = connection_key
        self.pgcompleter: PGCompleter = None
        self.is_connected: bool = False
        self.queue: Queue = Queue()
        self.is_canceled = False
        self.intellisense_complete: threading.Event = threading.Event()
        # Start metadata refresh so operations can be completed
        completion_refresher = CompletionRefresher(connection)
        completion_refresher.refresh(self._on_completions_refreshed)
        # Start the thread to process work
        thread = threading.Thread(target=self._process_queue)
        thread.daemon = True
        thread.start()

    # PUBLIC METHODS ###############################################
    def add_operation(self, operation: QueuedOperation) -> None:
        # TODO should we wait for a fixed time?
        if self.is_canceled:
            raise RuntimeError('Queue has been canceled, no more operations should be send to it')   # TODO Localize 
        self.queue.put(operation)

    def cancel(self):
        """
        Cancels queue processing. Next time through the while loop the processor will break and the thread
        will complete
        """
        self.is_canceled = True

    # IMPLEMENTATION DETAILS ###############################################
    def _on_completions_refreshed(self, new_completer: PGCompleter):
        self.pgcompleter = new_completer
        self.is_connected = True
        self.intellisense_complete.set()

    def _process_queue(self):
        """
        Threaded operation that runs to process the queue.
        Thread completes on cancelation
        """
        while not self.is_canceled:
            try:
                operation: QueuedOperation = self.queue.get(True, POLL_TIMEOUT)
                if self.is_canceled:
                    break
                
                run_timeout_task = not self.is_connected
                if self.is_connected:
                    run_timeout_task = operation.task(self.pgcompleter)
                if run_timeout_task:
                    operation.timeout_task()
                
                self.queue.task_done()
            except Empty as e:
                # Nothing to process in the timeout period
                pass


class OperationsQueue:
    """
    Handles requests to queue operations that require a connection. Currently this works
    by having a single queue per connection.
    """

    def __init__(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self.lock: threading.Lock = threading.Lock()
        self.queue_map: Dict[str, ConnectedQueue] = {}

    # PUBLIC METHODS ###############################################
    def add_operation(self, operation: QueuedOperation):
        """
        Adds an operation to the correct queue. Raises KeyError if no queue exists for this connection
        """
        with self.lock:
            # Get the queue or throw KeyError if not found
            queue: ConnectedQueue = self.queue_map[operation.key]
            queue.add_operation(operation)

    def has_connection_context(self, conn_info: ConnectionInfo) -> bool:
        """
        Checks if there's a connection context for a given connection in the map.
        Intentional does not lock as this is intended for quick lookup
        """
        key: str = self._create_key(conn_info)
        return key in self.queue_map

    def add_connection_context(self, conn_info: ConnectionInfo, overwrite=False) -> ConnectionContext:
        """
        Adds a connection context and returns the notification event.
        If a connection queue exists alread, will overwrite if necesary
        """
        with self.lock:
            key: str = self._create_key(conn_info)
            queue: ConnectedQueue = self.queue_map.get(key)
            if queue:
                if overwrite:
                    queue.cancel()
                    self.queue_map.pop(key, None)
                else:
                    # Notify ready and return immediately, the queue exists
                    return queue.intellisense_complete
            # Connection is required
            conn = self._create_connection(key, conn_info)
            # Create a new queue and return the awaitable event for intellisense to be ready
            queue = ConnectedQueue(key, conn)
            return ConnectionContext(key, queue.intellisense_complete)

    def disconnect(self, connection_key: str):
        """
        Disconnects a connection that was used for intellisense
        """
        with self.lock:
            # Pop the key from the queue as it's no longer needed
            queue: ConnectedQueue = self.queue_map.pop(connection_key, None)
            if queue:
                queue.cancel()
                key_uri = INTELLISENSE_URI + connection_key
                try:
                    self._connection_service.disconnect(key_uri, ConnectionType.INTELLISENSE)
                except Exception as ex:
                    self._log_exception('error during disconnect, ignoring as assume already disconnected: {0}'.format(ex))

    # IMPLEMENTATION DETAILS ###############################################
    def _create_key(self, conn_info: ConnectionInfo) -> str:
        return '{0}_{1}_{2}'.format(conn_info.details.server_name, conn_info.details.database_name, conn_info.details.user_name)

    def _create_connection(self, connection_key: str, conn_info: ConnectionInfo) -> Optional[psycopg2.extensions.connection]:
        conn_service = self._connection_service
        key_uri = INTELLISENSE_URI + connection_key
        connect_request = ConnectRequestParams(conn_info.details, key_uri, ConnectionType.INTELLISENSE)
        connect_result = conn_service.connect(connect_request)
        if connect_result.error_message is not None:
            raise RuntimeError(connect_result.error_message)

        connection = conn_service.get_connection(key_uri, ConnectionType.INTELLISENSE)
        return connection

    @property
    def _connection_service(self) -> ConnectionService:
        return  self._service_provider[utils.constants.CONNECTION_SERVICE_NAME]

    def _log_exception(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.exception(message)

    def _log_info(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.info(message)
