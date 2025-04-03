from abc import ABC, abstractmethod
from typing import Any, Callable

from psycopg import Connection
from psycopg.rows import TupleRow

from ossdbtoolsservice.connection.contracts import AzureToken, ConnectionDetails


class ConnectionClassFactoryBase(ABC):
    """
    Factory class to create a PostgreSQL connection class.
    """

    @abstractmethod
    def create_connection_class(
        self,
        details: ConnectionDetails,
        store_connection_error: Callable[[ConnectionDetails, Exception], None],
        maybe_refresh_azure_token: Callable[[ConnectionDetails], AzureToken | None] | None,
    ) -> type[Connection[TupleRow]]:
        """
        Create a PostgreSQL connection object.

        :param details: The connection details that are used to create the connections.
        :param store_connection_error: A callable to store the connection error.
            This is used to store the connection errors in the connection manager.
            These can be communicated as part of an error response to the user
            if the pool times out.
        :param maybe_refresh_azure_token: A callable to fetch the token if needed.
            If the token does not need to be refreshed, this function should return None.
            Otherwise return the new token.
            If not supplied, no azure refresh will be attempted.
        :return: A PostgreSQL connection object.
        """
        pass


class ConnectionClassFactory(ConnectionClassFactoryBase):
    """
    Factory class to create a PostgreSQL connection class.
    """

    @staticmethod
    def maybe_handle_azure_token(
        details: ConnectionDetails,
        maybe_refresh_azure_token: Callable[[ConnectionDetails], AzureToken | None] | None,
        kwargs: dict[str, Any],
    ) -> None:
        """
        Handle the azure token refresh if needed.
        """
        if not details.azure_token or not maybe_refresh_azure_token:
            return

        new_azure_token = maybe_refresh_azure_token(details)
        if new_azure_token:
            kwargs["password"] = new_azure_token

    def create_connection_class(
        self,
        details: ConnectionDetails,
        store_connection_error: Callable[[ConnectionDetails, Exception], None],
        maybe_refresh_azure_token: Callable[[ConnectionDetails], AzureToken | None] | None,
    ) -> type[Connection[TupleRow]]:
        class PGTSConnection(Connection[TupleRow]):
            @classmethod
            def connect(cls, *args: Any, **kwargs: Any) -> "PGTSConnection":
                try:
                    # If the connection is using an Entra token, we need to be able to
                    # refresh that token when it expires. This is done by creating a new
                    # connection class that checks the token expiration and refreshes
                    # it if needed.
                    self.maybe_handle_azure_token(
                        details, maybe_refresh_azure_token, kwargs
                    )

                    return super().connect(*args, **kwargs)
                except Exception as e:
                    store_connection_error(details, e)
                    raise

        return PGTSConnection
