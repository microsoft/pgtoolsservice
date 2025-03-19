# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import logging
import queue
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool, PoolTimeout

from ossdbtoolsservice.connection.contracts import (
    AzureToken,
    ConnectionDetails,
    ConnectionSummary,
    ConnectionType,
    ServerInfo,
)
from ossdbtoolsservice.connection.core.connection_class import (
    ConnectionClassFactory,
    ConnectionClassFactoryBase,
)
from ossdbtoolsservice.connection.core.errors import GetConnectionTimeout
from ossdbtoolsservice.connection.core.owner_connection_info import OwnerConnectionInfo
from ossdbtoolsservice.connection.core.pooled_connection import PooledConnection
from ossdbtoolsservice.connection.core.server_connection import ServerConnection
from ossdbtoolsservice.workspace.contracts.did_change_config_notification import Configuration


@dataclass
class ConnectionTaskResponse:
    """A response to a connection task.

    Args:
        result: The result of the task.
        error: The error that occurred during the task.
    """

    result: Any = None
    error: Exception | None = None


@dataclass
class ConnectionTaskMessage:
    """A task to be processed by the connection manager.

    Args:
        task: The function to be executed.
        args: The arguments to pass to the function.
        response: A response object to store the result of the task.
        event: An event to signal when the task is complete.
    """

    task: Callable
    args: tuple
    response: ConnectionTaskResponse
    event: threading.Event


class ConnectionManager:
    def __init__(
        self,
        fetch_azure_token: Callable[[str, str | None], AzureToken] | None = None,
        max_pool_size: int = 10,
        connection_class_factory: ConnectionClassFactoryBase | None = None,
        logger: logging.Logger | None = None,
        timeout_override: int | None = None,
    ) -> None:
        """Initialize the connection manager.

        Args:
            fetch_azure_token: A function to fetch the Azure token.
            max_pool_size: The maximum size of the connection pool.
            connection_class_factory: A factory to create the connection class.
            logger: A logger to use for logging.
            timeout_override: If True, will override the timeout for the connection pool.
        """
        self.connection_class_factory = connection_class_factory or ConnectionClassFactory()
        self._lock = threading.RLock()  # Use RLock to allow re-entrance
        self._pool_worker_lock = threading.Lock()  # Lock for pool worker threads
        self._details_to_pools: dict[int, ConnectionPool] = {}
        self._details_to_owner_uri: dict[int, list[str]] = {}
        self._owner_uri_to_details: dict[str, tuple[ConnectionDetails, ConnectionPool]] = {}
        self._owner_uri_to_active_tx_connection: dict[
            str, tuple[ServerConnection, ConnectionPool]
        ] = {}
        self._owner_uri_to_orphaned_connection: dict[
            str, dict[ConnectionType, ServerConnection]
        ] = {}
        self._owner_uri_to_conn_info: dict[str, OwnerConnectionInfo] = {}

        self._fetch_azure_token = fetch_azure_token
        self._max_pool_size = max_pool_size
        self._logger = logger or logging.getLogger(__name__)
        self._timeout_override = timeout_override

        # Hold on to connection errors to be able to report them
        # to the user on connection failure. By default, psycopg_pool
        # will raise a PoolTimeout exception without any details
        # if connections cannot be established after a timeout.
        self._details_to_connection_errors: dict[int, list[Exception]] = {}

        # Process connection and disconnection requests in a background thread
        # to ensure propert ordering of requests. This avoids situations where
        # repeated connect/disconnect requests are processed out of order.
        self._task_queue = queue.Queue[ConnectionTaskMessage]()
        self._request_thread = threading.Thread(
            target=self._process_tasks, name="ConnectionManagerWorker", daemon=True
        )
        self._request_thread.start()

    def _process_tasks(self) -> None:
        while True:
            message = self._task_queue.get()
            try:
                result = message.task(*message.args)
                message.response.result = result
                message.event.set()
            except Exception as e:
                # Handle exceptions in the task processing
                message.response.error = e
                message.event.set()

    def _run_task(self, task: Callable, args: tuple) -> Any:
        event = threading.Event()
        response = ConnectionTaskResponse()
        self._task_queue.put(ConnectionTaskMessage(task, args, response, event))
        event.wait()
        if response.error:
            raise response.error
        return response.result

    def connect(
        self, owner_uri: str, details: ConnectionDetails, config: Configuration | None = None
    ) -> OwnerConnectionInfo:
        """Connect to the database using the given details.
        This will create a new connection pool if one does not already exist.

        Args:
            owner_uri: The owner URI of the connection.
            details: The connection details to use.
            config: The configuration to use.
        Returns:
            The connection complete params for the connection.
        """
        return self._run_task(self._connect, (owner_uri, details, config))

    def _connect(
        self, owner_uri: str, details: ConnectionDetails, config: Configuration | None = None
    ) -> OwnerConnectionInfo:
        with self._lock:
            details_hash = details.to_hash()

            # Check if the URI is already associated with a connection pool.
            existing_connection_complete_params = self._owner_uri_to_conn_info.get(owner_uri)
            if existing_connection_complete_params is not None:
                existing_associated_details_and_pool = self._owner_uri_to_details.get(
                    owner_uri
                )

                if existing_associated_details_and_pool is not None:
                    existing_details, _ = existing_associated_details_and_pool
                    # If so, check if the details match.
                    if existing_details.to_hash() == details_hash:
                        # If so, nothing to do.
                        return existing_connection_complete_params
                    else:
                        # If not, disconnect the owner_uri from the existing connection pool.
                        # Call _disconnect directly, as we are processing a task.
                        self._disconnect(owner_uri)

            pool = self._details_to_pools.get(details_hash)
            if pool is None:
                # Create a new pool.
                try:
                    pool = self._create_connection_pool(details, config)
                except PoolTimeout as e:
                    # If the pool is empty, this means that the connection
                    # could not be established.
                    conn_str = self._get_user_facing_conn_str(details)

                    # check if we have any connection errors to report
                    connection_error_message = self._get_and_clear_connection_errors(
                        details_hash
                    )

                    raise ConnectionError(
                        f"Could not connect to {conn_str}. Pool initialization timed out."
                        + connection_error_message
                    ) from e
                self._details_to_pools[details_hash] = pool
            # Associate the owner URI with the connection pool.
            self._owner_uri_to_details[owner_uri] = (details, pool)
            self._details_to_owner_uri.setdefault(details_hash, []).append(owner_uri)
            with pool.connection() as conn:
                owner_conn_info = self._build_owner_connection_info(
                    owner_uri, details, ServerConnection(conn)
                )
                self._owner_uri_to_conn_info[owner_uri] = owner_conn_info
                return owner_conn_info

    def disconnect(self, owner_uri: str) -> bool:
        """Disconnect the owner URI from the connection pool.
        This will close the connection and remove it from the pool.
        If the connection is in a transaction, it will be closed and the transaction
        will be rolled back.
        Args:
            owner_uri: The owner URI to disconnect.
        Returns:
            True if the connection was disconnected, False if no connection was found.
        """
        return self._run_task(self._disconnect, (owner_uri,))

    def _disconnect(self, owner_uri: str) -> bool:
        with self._lock:
            # Remove connections currently in transaction.
            if owner_uri in self._owner_uri_to_active_tx_connection:
                conn, pool = self._owner_uri_to_active_tx_connection.pop(owner_uri)
                conn.close()
                pool.putconn(conn.connection)

            # Remove orphaned connections.
            if owner_uri in self._owner_uri_to_orphaned_connection:
                connections = self._owner_uri_to_orphaned_connection.pop(owner_uri)
                for conn in connections.values():
                    conn.return_to_pool()

            # Remove the owner URI from the details to owner URI mapping.
            details_and_pool = self._owner_uri_to_details.pop(owner_uri, None)
            if details_and_pool:
                details = details_and_pool[0]
                details_hash = details.to_hash()
                pool_owner_uris = self._details_to_owner_uri.get(details_hash, [])
                if owner_uri in pool_owner_uris:
                    pool_owner_uris.remove(owner_uri)

                # If no owner URIs are left, close the pool.
                if not pool_owner_uris:
                    pool = self._details_to_pools.pop(details_hash, None)
                    if pool:
                        pool.close()

            # Remove the connection complete params for the owner URI.
            if owner_uri in self._owner_uri_to_conn_info:
                del self._owner_uri_to_conn_info[owner_uri]
                return True
            else:
                return False

    def get_pooled_connection(self, owner_uri: str) -> PooledConnection | None:
        """Get a pooled connection for the given owner URI.

        The pooled connection is a context manager that will produce a connection
        that calling code can use to execute statements.
        If there is already a connection in transaction for the owner URI,
        that connection will be returned from the context manager.
        Otherwise a connection from the poolwill be returned.

        Args:
            owner_uri: The owner URI of the connection.
        Returns:
            The pooled connection if a connection is established
            for the owner_uri, None otherwise.
        """
        with self._lock:
            # Check if the owner URI is already associated with an existing connection.
            if owner_uri in self._owner_uri_to_active_tx_connection:
                # If so, return the existing connection.
                conn, pool = self._owner_uri_to_active_tx_connection[owner_uri]
                return PooledConnection(
                    get_connection=lambda: conn,
                    put_connection=lambda conn: self._put_connection(conn, pool, owner_uri),
                )
            elif owner_uri in self._owner_uri_to_details:
                # If the owner URI is associated with a connection pool, return it.
                details, pool = self._owner_uri_to_details[owner_uri]
                return PooledConnection(
                    get_connection=lambda: self._get_connection(pool, details),
                    put_connection=lambda conn: self._put_connection(conn, pool, owner_uri),
                )
            else:
                return None

    def get_orphaned_connection(
        self, owner_uri: str, connection_type: ConnectionType
    ) -> ServerConnection | None:
        """Gets a connection that is not tracked with the pool it comes from.

        This is to support legacy code that does not use the connection pool.
        The connection will need to be managed by the caller.

        Args:
            owner_uri: The owner URI of the connection.
            connection_type: The type of connection to get.
        Returns:
            The connection if found, None otherwise.
        """
        with self._lock:
            if owner_uri in self._owner_uri_to_orphaned_connection:
                # If the owner URI is already associated with an orphaned connection of
                # the same type, return it.
                # Check the connection first, same way the pool does.
                # If the connection is not valid, remove it from the map,
                # so a new connection can be created.
                connections = self._owner_uri_to_orphaned_connection[owner_uri]
                if connection_type in connections:
                    conn = connections[connection_type]
                    try:
                        conn.check()
                        return conn
                    except Exception:
                        # If the connection is not valid, remove it from the map
                        # and return it to the pool. The pool will discard it.
                        conn.return_to_pool()
                        del connections[connection_type]
                        if not connections:
                            del self._owner_uri_to_orphaned_connection[owner_uri]
            if owner_uri in self._owner_uri_to_details:
                # If the owner URI is associated with a connection pool, get a new connection.
                details, pool = self._owner_uri_to_details[owner_uri]
                conn = self._get_connection(pool, details, True)
                conn.autocommit = True
                # Set the application name to show the connection type.
                application_name = conn.application_name or ""
                application_name = f"{application_name} - {connection_type.value}"
                conn.execute_statement("SET application_name = %s", [application_name])
                # Store the connection in the orphaned connection map.
                if owner_uri not in self._owner_uri_to_orphaned_connection:
                    self._owner_uri_to_orphaned_connection[owner_uri] = {}
                self._owner_uri_to_orphaned_connection[owner_uri][connection_type] = conn
                return conn
            else:
                return None

    def get_connection_info(self, owner_uri: str) -> OwnerConnectionInfo | None:
        """Get the connection complete params for the given owner URI."""
        with self._lock:
            return self._owner_uri_to_conn_info.get(owner_uri)

    def close(self) -> None:
        with self._lock:
            for conn in self._owner_uri_to_active_tx_connection.values():
                conn[0].close()
            for pool in self._details_to_pools.values():
                pool.close()
            self._details_to_pools.clear()
            self._details_to_owner_uri.clear()
            self._owner_uri_to_details.clear()
            self._owner_uri_to_active_tx_connection.clear()
            self._owner_uri_to_orphaned_connection.clear()
            self._owner_uri_to_conn_info.clear()
            self._details_to_connection_errors.clear()

    def get_pool_stats(self) -> dict[str, Any]:
        """Get the pool stats for all pools."""
        with self._lock:
            stats = {}
            for _, pool in self._details_to_pools.items():
                pool_stats = pool.get_stats()
                stats[pool.name] = {
                    **pool_stats,
                }
            return stats

    def set_fetch_azure_token(
        self, fetch_azure_token: Callable[[str, str | None], AzureToken]
    ) -> None:
        """Set the function to fetch the Azure token.

        Args:
            fetch_azure_token: The function to fetch the Azure token.
        """
        self._fetch_azure_token = fetch_azure_token

    def _get_connection(
        self, pool: ConnectionPool, details: ConnectionDetails, is_orphan: bool = False
    ) -> ServerConnection:
        try:
            conn = pool.getconn()

            # This is a connection not in a transaction, otherwise it would
            # not have been returned from the pool.
            # Set autocommit to True.
            conn.autocommit = True
            # If this is an orphaned connection, set the pool so that
            # it can be manually returned to the pool.
            return ServerConnection(conn, pool if is_orphan else None)
        except PoolTimeout as e:
            stats = pool.get_stats()
            pool_size = stats.get("pool_size", 0)
            if pool_size == 0:
                # If the pool is empty, this means that the connection
                # could not be established.
                conn_str = self._get_user_facing_conn_str(details)
                raise ConnectionError(f"Could not connect to {conn_str}.") from e
            # If the pool is not empty, but we timed out, this means
            # that the pool is full and we need to wait for a connection.
            max_size = stats.get("pool_max", 0)
            active_tx = 0
            for owner_uri in self._details_to_owner_uri.get(details.to_hash(), []):
                active_tx += 1 if owner_uri in self._owner_uri_to_active_tx_connection else 0
            connect_error_message = self._get_and_clear_connection_errors(details.to_hash())
            raise GetConnectionTimeout(
                pool_size=pool_size,
                pool_max=max_size,
                active_tx=active_tx,
                connection_error_message=connect_error_message,
            ) from e

    def _put_connection(
        self,
        conn: ServerConnection,
        pool: ConnectionPool,
        owner_uri: str,
    ) -> None:
        with self._lock:
            # Check if the connection is in a transaction.
            # If so, we can't put it back in the pool.
            if conn.transaction_in_trans:
                # Store the connection in the active transaction map.
                self._owner_uri_to_active_tx_connection[owner_uri] = (conn, pool)
            elif conn.transaction_in_error and not conn.autocommit:
                # Same for if the transaction is in error.
                # If the user started a transaction, keep the transaction open
                # so they may debug, and explicitly all ROLLBACK or ROLLBACK TO SAVEPOINT.
                #
                # If the connection has autocommit set to True, the transaction
                # is managed by the server and should be rolled back automatically.
                # We can place the connection back into the pool.
                self._owner_uri_to_active_tx_connection[owner_uri] = (conn, pool)
            else:
                # If the connection was previously in a transaction,
                # remove it from the active transaction map.
                if owner_uri in self._owner_uri_to_active_tx_connection:
                    del self._owner_uri_to_active_tx_connection[owner_uri]

                # Set autocommit to True, as the connection is not in a transaction.
                conn.autocommit = True
                # Return the connection to the pool.
                pool.putconn(conn.connection)

    def _create_connection_pool(
        self, details: ConnectionDetails, config: Configuration | None = None
    ) -> ConnectionPool:
        connection_class = self.connection_class_factory.create_connection_class(
            details,
            self._store_connection_error,
            self._maybe_refresh_azure_token if self._fetch_azure_token else None,
        )
        # Create a new connection pool.
        pool = ConnectionPool(
            name=str(details.to_hash()),
            min_size=1,
            max_size=self._max_pool_size,
            timeout=self._timeout_override or details.connect_timeout,
            open=False,
            check=ConnectionPool.check_connection,
            kwargs=details.get_connection_params(config),
            connection_class=connection_class,
        )

        # Open and wait for the first connection to be establshed
        # to avoid creating mutliple connections when not needed.
        pool.open(wait=True, timeout=self._timeout_override or details.connect_timeout)
        return pool

    def _build_owner_connection_info(
        self,
        owner_uri: str,
        connection_details: ConnectionDetails,
        connection: ServerConnection,
    ) -> OwnerConnectionInfo:
        """Build information about the connection for the owner URI"""
        connection_summary = ConnectionSummary(
            server_name=connection.host_name,
            database_name=connection.database_name,
            user_name=connection.user_name,
        )

        connection_id = uuid.uuid4().hex
        connection_summary = connection_summary
        owner_uri = owner_uri
        server_info = self._get_server_info(connection)

        return OwnerConnectionInfo(
            owner_uri=owner_uri,
            connection_id=connection_id,
            server_info=server_info,
            connection_summary=connection_summary,
            connection_details=connection_details,
        )

    def _get_server_info(self, connection: ServerConnection) -> ServerInfo:
        """Build the server info response for a connection

        Args:
            connection: The connection to get the server info for.
        Returns:
            The server info for the connection. Includes the server version as a tuple of int.
        """
        server = "PostgreSQL"
        host = connection.host_name
        is_cloud = host.endswith("database.azure.com") or host.endswith(
            "database.windows.net"
        )
        server_version = (
            str(connection.server_version[0])
            + "."
            + str(connection.server_version[1])
            + "."
            + str(connection.server_version[2])
        )
        return ServerInfo(server=server, server_version=server_version, is_cloud=is_cloud)

    def _maybe_refresh_azure_token(self, details: ConnectionDetails) -> AzureToken | None:
        """Refresh the Azure token for the given connection details if need be.
        Update the connection details with the new token.

        Args:
            details: The connection details to use.
        Returns:
            The refreshed Azure token if refresh occurred, None otherwise.
        """
        if self._fetch_azure_token is None or not details.azure_token:
            # If the token is not set, return None.
            return None

        # Operate in the lock to avoid multiple pool worker threads
        # trying to refresh the token at the same time.
        with self._pool_worker_lock:
            azure_token = details.azure_token
            if azure_token.is_azure_token_expired():
                # Get the account ID and tenant ID from the connection details
                account_id = details.azure_account_id
                tenant_id = details.azure_tenant_id
                if not account_id:
                    # This is a bug, the account ID and tenant ID should be
                    # set if the token is set.
                    raise ValueError(
                        "Azure account ID must be provided to refresh the token."
                    )
                new_azure_token = self._fetch_azure_token(account_id, tenant_id)
                details.azure_token = new_azure_token
                return new_azure_token
            return None

    def _store_connection_error(self, details: ConnectionDetails, error: Exception) -> None:
        """Store the connection error for the given connection details.

        Args:
            details: The connection details to use.
            error: The error to store.
        """
        self._logger.error(
            f"Connection error for {self._get_user_facing_conn_str(details)}: {error}"
        )
        details_hash = details.to_hash()
        with self._pool_worker_lock:
            self._details_to_connection_errors.setdefault(details_hash, []).append(error)

    def _get_and_clear_connection_errors(self, details_hash: int) -> str:
        connection_errors = self._details_to_connection_errors.get(details_hash)
        connection_error_messages: list[str] = []
        if connection_errors:
            seen_errors = set()
            for error in connection_errors:
                if str(error) not in seen_errors:
                    seen_errors.add(str(error))
                    connection_error_messages.append(str(error))
        if connection_error_messages:
            if len(connection_error_messages) > 1:
                connection_error_message = "\nConnection errors:\n"
            else:
                connection_error_message = "\nConnection error:\n"
            connection_error_message += "\n".join(connection_error_messages)
        else:
            connection_error_message = ""

        # Clear connection errors as they will have been reported
        self._details_to_connection_errors.pop(details_hash, None)
        return connection_error_message

    def _get_user_facing_conn_str(self, details: ConnectionDetails) -> str:
        """Get the user facing connection string for the given connection details.

        Args:
            details: The connection details to use.
        Returns:
            The user facing connection string.
        """
        conn_params = details.get_connection_params()
        conn_params.pop("application_name", None)
        if "password" in conn_params:
            if details.azure_token:
                conn_params.pop("password")
            else:
                conn_params["password"] = "*****"
        conn_str = make_conninfo(**conn_params)
        return conn_str
