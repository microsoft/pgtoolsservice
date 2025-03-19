from typing import Any, Callable

from ossdbtoolsservice.connection.core.server_connection import ServerConnection


class PooledConnection:
    """A context manager for connections.

    This class is used to produce a connection for the duration of a context.
    It is used to ensure that connections are returned to the pool when they are
    no longer needed.

    This clas can be used as a context manager only once. After the context
    manager is exited, the connection is returned to the pool and the context
    manager cannot be used again. If you need to use the connection again,
    you need to create a pooled connection.

    Usage:
        # Get a pooled connection from the connection manager
        pooled_connection = context_manager.get_pooled_connection(owner_uri)
        if pooled_connection is None:
            # The owner uri is not connected
            ...
        with pooled_connection as connection:
            # Use the connection
            ...
    """

    def __init__(
        self,
        get_connection: Callable[[], ServerConnection],
        put_connection: Callable[[ServerConnection], None],
    ) -> None:
        self._get_connection = get_connection
        self._put_connection = put_connection
        self._connection: ServerConnection | None = None
        self._is_closed = False

    def __enter__(self) -> ServerConnection:
        """Get a connection from the pool."""
        if self._is_closed:
            raise RuntimeError("Cannot re-use a pooled connection after it has been closed.")

        self._connection = self._get_connection()
        return self._connection

    def __exit__(
        self, exc_type: type[Exception], exc_value: Exception, traceback: Any
    ) -> None:
        self._is_closed = True
        if self._connection is not None:
            self._put_connection(self._connection)
