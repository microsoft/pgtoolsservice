from typing import Any, Callable
from unittest import mock

import pytest
from psycopg import Connection, sql
from psycopg.pq import TransactionStatus
from psycopg.rows import TupleRow
from psycopg_pool import ConnectionPool

from ossdbtoolsservice.connection.contracts import AzureToken, ConnectionDetails
from ossdbtoolsservice.connection.core.connection_class import (
    ConnectionClassFactory,
    ConnectionClassFactoryBase,
)
from ossdbtoolsservice.connection.core.connection_manager import (
    ConnectionManager,
)
from ossdbtoolsservice.connection.core.server_connection import Params
from ossdbtoolsservice.workspace.contracts.did_change_config_notification import Configuration


class MockConnectionClassFactory(ConnectionClassFactoryBase):
    def __init__(self) -> None:
        self.queries_executed: list[tuple[sql.SQL, Params | None]] = []
        self.connection_errors: dict[ConnectionDetails, list[Exception]] = {}

    def create_connection_class(
        self,
        details: ConnectionDetails,
        store_connection_error: Callable[[ConnectionDetails, Exception], None],
        get_azure_token: Callable[[ConnectionDetails], AzureToken | None] | None,
    ) -> type[Connection[TupleRow]]:
        def get_mock_connection(*args: Any, **kwargs: Any) -> Connection[TupleRow]:
            nonlocal get_azure_token
            ConnectionClassFactory.maybe_set_azure_token(details, get_azure_token, kwargs)

            # MOCK: Connection Info
            mock_connection_info = mock.Mock()
            mock_connection_info.get_parameters = mock.Mock(
                return_value=details.get_connection_params()
            )
            mock_connection_info.transaction_status = TransactionStatus.IDLE
            mock_connection_info.server_version = "170400"

            # MOCK: Cursor
            mock_cursor = mock.Mock()

            # Save the query from the first parameter to self._queries_executed.
            def capture_query(query: sql.SQL, params: Params | None = None) -> None:
                self.queries_executed.append((query, params))

            mock_cursor.execute = mock.Mock(side_effect=capture_query)

            # MOCK: Connection
            mock_connection = mock.Mock(name="MockConnection")
            mock_connection.info = mock_connection_info
            mock_connection.autocommit = mock.Mock()
            mock_connection.__enter__ = mock.Mock(return_value=None)
            mock_connection.__exit__ = mock.Mock(return_value=None)
            mock_connection.cursor = mock.Mock()
            mock_connection.cursor.return_value.__enter__ = mock.Mock(
                return_value=mock_cursor
            )
            mock_connection.cursor.return_value.__exit__ = mock.Mock(return_value=None)
            return mock_connection

        mock_connection_class = mock.Mock()
        mock_connection_class.connect.side_effect = get_mock_connection

        return mock_connection_class  # type: ignore[return-value]


class StubConnectionManager(ConnectionManager):
    """Test subclass of ConnectionManager that overrides _create_connection_pool"""

    def __init__(self) -> None:
        super().__init__(mock.MagicMock)
        self.mock_connection_class_factory = MockConnectionClassFactory()

    def _create_connection_pool(
        self, details: ConnectionDetails, config: Configuration | None = None
    ) -> ConnectionPool:
        mock_connection_class = self.mock_connection_class_factory.create_connection_class(
            details, lambda x, y: None, lambda x: None
        )

        # MOCK: Connection Pool
        mock_connection_pool = mock.Mock(spec=ConnectionPool)
        mock_connection_context = mock.Mock()
        mock_connection_context.__enter__ = mock.Mock(
            side_effect=mock_connection_class.connect
        )
        mock_connection_context.__exit__ = mock.Mock(return_value=None)
        mock_connection_pool.connection = mock.Mock(return_value=mock_connection_context)
        mock_connection_pool.getconn = mock.Mock(side_effect=mock_connection_class.connect)
        mock_connection_pool.putconn = mock.Mock()
        mock_connection_pool.close = mock.Mock()
        mock_connection_pool.wait = mock.Mock()

        return mock_connection_pool

    def get_connection_pool(self, details: ConnectionDetails) -> ConnectionPool | None:
        return self._details_to_pools.get(details.to_hash())


@pytest.fixture(scope="function")
def mock_connection_class_factory() -> MockConnectionClassFactory:
    """Fixture for creating a testable connection class factory."""
    return MockConnectionClassFactory()


@pytest.fixture(scope="function")
def stub_connection_manager() -> StubConnectionManager:
    """Fixture for creating a testable connection manager."""
    return StubConnectionManager()


@pytest.fixture(scope="function")
def connection_manager(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> ConnectionManager:
    """Fixture for creating a testable connection manager."""
    return ConnectionManager(
        connection_class_factory=mock_connection_class_factory,
    )
