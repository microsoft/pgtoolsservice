# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""A module that handles queueing"""

import threading
from logging import Logger
from queue import Queue
from typing import Callable, Optional

from prompt_toolkit.completion import Completer

from ossdbtoolsservice.connection import (
    ConnectionService,
    OwnerConnectionInfo,
    PooledConnection,
)
from ossdbtoolsservice.hosting import ServiceProvider
from ossdbtoolsservice.language.completion_refresher import CompletionRefresher
from ossdbtoolsservice.utils import constants

INTELLISENSE_URI = "intellisense://"


class ConnectionContext:
    """Context information needed to look up connections"""

    def __init__(self, key: str, logger: Logger | None = None) -> None:
        self.key = key
        self.intellisense_complete: threading.Event = threading.Event()
        self.completer: Completer | None = None
        self.is_connected: bool = False
        self.logger: Logger | None = logger

    def refresh_metadata(self, pooled_connection: PooledConnection) -> None:
        # Start metadata refresh so operations can be completed
        completion_refresher = CompletionRefresher(pooled_connection, self.logger)
        completion_refresher.refresh(self._on_completions_refreshed)

    # IMPLEMENTATION DETAILS ###############################################
    def _on_completions_refreshed(self, new_completer: Completer) -> None:
        self.completer = new_completer
        self.is_connected = True
        self.intellisense_complete.set()


class QueuedOperation:
    """Information about an operation to be queued"""

    def __init__(
        self,
        key: str,
        task: Callable[[ConnectionContext], bool],
        timeout_task: Callable[[], None],
    ) -> None:
        """
        Initializes a queued operation with a key defining the connection it maps to,
        a task to be run for a connected queue, and a timeout task. Currently the timeout
        task is just used if the queue is not yet connected
        """
        self.key = key
        self.task: Callable[[ConnectionContext], bool] = task
        self.timeout_task: Callable[[], None] = timeout_task
        self.context: ConnectionContext | None = None


class OperationsQueue:
    """
    Handles requests to queue operations that require a connection. Currently this works
    by having a single queue per connection.
    """

    # CONSTANTS ############################################################
    OPERATIONS_THREAD_NAME = "LANG_SVC_Operations"

    def __init__(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self.lock: threading.RLock = threading.RLock()
        self.queue: Queue = Queue()
        self._context_map: dict[str, ConnectionContext] = {}
        self.stop_requested = False
        # TODO consider thread pool for multiple messages? Or full
        # Process queue using multi-threading
        self._operations_consumer: threading.Thread | None = None

    # PUBLIC METHODS ###############################################
    def start(self) -> None:
        """
        Starts the thread that processes operations
        """
        self._log_info("Language Service Operations Queue starting...")
        self._operations_consumer = threading.Thread(
            target=self._process_operations, args=(), name=self.OPERATIONS_THREAD_NAME
        )
        self._operations_consumer.daemon = True
        self._operations_consumer.start()

    def stop(self) -> None:
        self.stop_requested = True
        # Enqueue None to optimistically unblock output thread
        # so it can check for the cancellation flag
        self.queue.put(None)
        self._log_info("Language Service Operations Queue stopping...")

    def add_operation(self, operation: QueuedOperation) -> None:
        """
        Adds an operation to the correct queue.
        Raises KeyError if no queue exists for this connection
        """
        if not operation:
            # Must throw in this case, as a None operation is used to close the
            # queue
            raise ValueError("Operation must not be None")
        with self.lock:
            # Get the connection context or throw KeyError if not found
            context: ConnectionContext = self._context_map[operation.key]
            operation.context = context
            self.queue.put(operation)

    def has_connection_context(self, conn_info: OwnerConnectionInfo) -> bool:
        """
        Checks if there's a connection context for a given connection in the map.
        Intentional does not lock as this is intended for quick lookup
        """
        key: str = OperationsQueue.create_key(conn_info)
        return key in self._context_map

    def add_connection_context(
        self, conn_info: OwnerConnectionInfo, overwrite: bool = False
    ) -> ConnectionContext:
        """
        Adds a connection context and returns the notification event.
        If a connection queue exists alread, will overwrite if necesary
        """
        with self.lock:
            key: str = OperationsQueue.create_key(conn_info)
            context: ConnectionContext | None = self._context_map.get(key)
            logger: Logger | None = self._service_provider.logger

            if context and not overwrite:
                # Notify ready and return immediately, the queue exists
                return context
            # Create the context and start refresh
            context = ConnectionContext(key, logger)
            pooled_connection = self._create_pooled_connection(conn_info.owner_uri)
            if not pooled_connection:
                raise RuntimeError("Failed to create connection for intellisense")
            context.refresh_metadata(pooled_connection)
            self._context_map[key] = context
            return context

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def create_key(cls, conn_info: OwnerConnectionInfo) -> str:
        """
        Creates a key uniquely identifying a ConnectionInfo object for use in caching
        """
        return (
            f"{conn_info.connection_details.server_name}|"
            f"{conn_info.connection_details.database_name}|"
            f"{conn_info.connection_details.user_name}"
        )

    def _create_pooled_connection(self, owner_uri: str) -> Optional[PooledConnection]:
        conn_service = self._connection_service
        connection = conn_service.get_pooled_connection(owner_uri)
        return connection

    def _process_operations(self) -> None:
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

    def execute_operation(self, operation: QueuedOperation) -> None:
        """
        Processes an operation. Separated for test purposes from the threaded logic
        """
        if operation is not None:
            # Try to process the task, falling back to the timeout
            # task if disconnected or regular task failed
            is_connected = operation.context is not None and operation.context.is_connected
            run_timeout_task = not is_connected
            if is_connected:
                assert operation.context is not None  # for type checker
                run_timeout_task = not operation.task(operation.context)
            if run_timeout_task:
                operation.timeout_task()

    @property
    def _connection_service(self) -> ConnectionService:
        return self._service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )

    def _log_exception(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.exception(message)

    def _log_info(self, message: str) -> None:
        logger = self._service_provider.logger
        if logger is not None:
            logger.info(message)

    def _log_thread_exception(self, ex: Exception) -> None:
        """
        Logs an exception if the logger is defined
        :param ex: Exception to log
        """
        self._log_exception(f"Thread {threading.currentThread()} encountered exception {ex}")
