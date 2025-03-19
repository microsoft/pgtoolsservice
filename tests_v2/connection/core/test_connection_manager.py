import threading
import time
from typing import Any
from unittest import mock

import pytest
from psycopg.pq import TransactionStatus

from ossdbtoolsservice.connection.contracts import (
    AzureToken,
    ConnectionDetails,
    ConnectionType,
)
from ossdbtoolsservice.connection.core.connection_manager import ConnectionManager
from ossdbtoolsservice.connection.core.errors import GetConnectionTimeout
from tests_v2.connection.conftest import MockConnectionClassFactory, StubConnectionManager


def get_connection_details() -> ConnectionDetails:
    """Create a mock connection details object."""
    return ConnectionDetails(
        options={
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
            "password": "test_password",
            "dbname": "test_db",
        }
    )


def get_azure_connection_details() -> ConnectionDetails:
    """Create a mock connection details object with Azure token."""
    return ConnectionDetails(
        options={
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
            "password": "test_password",
            "dbname": "test_db",
            "azureAccountId": "test_azure_account_id",
            "azureTenantId": "test_azure_tenant_id",
            "azureAccountToken": "test_azure_token",
            "azureTokenExpiry": int(time.time()) + 3600,  # Token valid for 1 hour
        }
    )


def test_connect_returns_valid_connection_info(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test connecting returns a valid connection info with expected details."""
    owner_uri = "test_owner_uri_1"
    details = get_connection_details()

    connection_manager = ConnectionManager(
        connection_class_factory=mock_connection_class_factory,
    )

    conn_info = connection_manager.connect(owner_uri, details)

    # Behavior: Connection info should contain the same connection details
    # (via hash) and a non-empty connection id
    assert conn_info.connection_details.to_hash() == details.to_hash()
    assert conn_info.connection_id


def test_reconnect_with_identical_details_returns_same_info(
    stub_connection_manager: StubConnectionManager,
) -> None:
    """Test that connecting twice with the same owner URI and identical
    details returns the same connection info."""
    owner_uri = "test_owner_uri_2"
    details = get_connection_details()

    conn_info1 = stub_connection_manager.connect(owner_uri, details)
    conn_info2 = stub_connection_manager.connect(owner_uri, details)

    # Behavior: The connection info returned should be equivalent (by connection id)
    assert conn_info1.connection_id == conn_info2.connection_id


def test_reconnect_with_different_details_creates_new_connection(
    stub_connection_manager: StubConnectionManager,
) -> None:
    """Test that calling connect with different details for the
    same owner URI effectively reconnects."""
    owner_uri = "test_owner_uri_3"
    details1 = get_connection_details()
    conn_info1 = stub_connection_manager.connect(owner_uri, details1)

    # Create modified connection details
    details2 = get_connection_details()
    details2.options["dbname"] = "different_db"

    conn_info2 = stub_connection_manager.connect(owner_uri, details2)

    # Behavior: New connection info should have a different connection id
    # (representing a new connection)
    assert conn_info1.connection_id != conn_info2.connection_id
    # And the connection details should reflect the new dbname.
    assert conn_info2.connection_details.options["dbname"] == "different_db"


def test_get_pooled_connection_normal(stub_connection_manager: StubConnectionManager) -> None:
    """Test that get_pooled_connection returns a usable connection via the context manager."""
    owner_uri = "test_owner_uri_4"
    details = get_connection_details()
    stub_connection_manager.connect(owner_uri, details)

    pooled_conn = stub_connection_manager.get_pooled_connection(owner_uri)
    assert pooled_conn is not None

    # Using the context manager should get a connection and afterward
    # trigger the pool's putconn.
    with pooled_conn as conn:
        # Behavior: the returned connection should have autocommit set to True.
        assert conn.autocommit is True
    # Verify that the pool's putconn was called.
    pool = stub_connection_manager._owner_uri_to_details[owner_uri][1]
    assert isinstance(pool, mock.Mock)
    pool.putconn.assert_called()


def test_get_pooled_connection_unknown(
    stub_connection_manager: StubConnectionManager,
) -> None:
    """Test that asking for a pooled connection for an unknown owner URI returns None."""
    pooled_conn = stub_connection_manager.get_pooled_connection("unknown_owner")
    assert pooled_conn is None


def test_get_orphaned_connection_valid(
    stub_connection_manager: StubConnectionManager,
) -> None:
    """Test that an orphaned connection is returned and
    its application name is set correctly."""
    owner_uri = "test_owner_uri_5"
    details = get_connection_details()
    details.options["application_name"] = "test_app_name"
    stub_connection_manager.connect(owner_uri, details)
    conn_type = ConnectionType.OBJECT_EXLPORER

    orphan_conn = stub_connection_manager.get_orphaned_connection(owner_uri, conn_type)
    assert orphan_conn is not None

    # Behavior: After retrieval, the orphan connection should have autocommit True
    assert orphan_conn.autocommit is True

    # The connection should have had a "SET application_name = %s" command executed.
    assert stub_connection_manager.mock_connection_class_factory.queries_executed, (
        "No queries executed, expected application name set"
    )
    for (
        query,
        params,
    ) in stub_connection_manager.mock_connection_class_factory.queries_executed:
        if query == "SET application_name = %s":
            assert params is not None
            params_list = list(params)
            assert len(params_list) == 1
            assert params_list[0] == "test_app_name - ObjectExplorer"
            break


def test_get_orphaned_connection_invalid_gets_recreated(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test that if an orphaned connection fails its check, a new connection is obtained."""
    owner_uri = "test_owner_uri_6"
    details = get_connection_details()

    connection_manager = ConnectionManager(
        connection_class_factory=mock_connection_class_factory,
    )
    connection_manager.connect(owner_uri, details)
    conn_type = ConnectionType.DEFAULT

    # Get an orphaned connection initially.
    orphan_conn = connection_manager.get_orphaned_connection(owner_uri, conn_type)
    assert orphan_conn is not None

    # Simulate that the existing orphan's check fails.
    conn = orphan_conn.connection
    assert isinstance(conn, mock.Mock)
    conn.execute.reset_mock()
    conn.pgconn = mock.Mock()
    conn.pgconn.transaction_status = TransactionStatus.UNKNOWN

    def throw_exception_on_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Invalid connection")

    conn.execute.side_effect = throw_exception_on_execute

    # Re-call get_orphaned_connection, which should cause the invalid one
    # to be recycled and a new one created.
    new_orphan_conn = connection_manager.get_orphaned_connection(owner_uri, conn_type)
    assert new_orphan_conn is not None
    # The new connection should be different from the old one.
    assert new_orphan_conn.connection is not orphan_conn.connection

    # And the new connection should have its application name command executed.
    conn.execute.assert_called()


def test_get_orphaned_connection_unknown_owner(
    stub_connection_manager: StubConnectionManager,
) -> None:
    """Test that getting an orphaned connection for an unrecognized owner URI returns None."""
    orphan_conn = stub_connection_manager.get_orphaned_connection(
        "unknown_owner", ConnectionType.DEFAULT
    )
    assert orphan_conn is None


def test_disconnect_behavior(stub_connection_manager: StubConnectionManager) -> None:
    """Test that disconnecting an owner URI makes connections unavailable behaviorally."""
    owner_uri = "test_owner_uri_7"
    details = get_connection_details()
    stub_connection_manager.connect(owner_uri, details)

    # Pre-disconnect, connection info should be available.
    assert stub_connection_manager.get_connection_info(owner_uri) is not None
    pool = stub_connection_manager.get_connection_pool(details)
    assert pool is not None
    # Disconnect
    result = stub_connection_manager.disconnect(owner_uri)
    assert result is True

    # Behavior: After disconnect, get_connection_info and get_pooled_connection
    # should return None.
    assert stub_connection_manager.get_connection_info(owner_uri) is None
    assert stub_connection_manager.get_pooled_connection(owner_uri) is None

    # Behavior: The connection pool should be closed.
    assert isinstance(pool, mock.Mock)
    pool.close.assert_called()


def test_disconnect_unknown_owner(stub_connection_manager: StubConnectionManager) -> None:
    """Test that disconnecting an unknown owner URI returns False."""
    result = stub_connection_manager.disconnect("unknown_owner")
    assert result is False


def test_close_releases_all_connections(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test that closing the connection manager prevents further connection retrieval."""
    # Connect a couple of owner URIs.
    owner_uri1 = "test_owner_uri_8"
    owner_uri2 = "test_owner_uri_9"
    details = get_connection_details()

    connection_manager = ConnectionManager(
        connection_class_factory=mock_connection_class_factory,
    )
    connection_manager.connect(owner_uri1, details)
    connection_manager.connect(owner_uri2, details)

    # Call close on the manager.
    connection_manager.close()

    # Behavior: After close, no connection info should be available.
    assert connection_manager.get_connection_info(owner_uri1) is None
    assert connection_manager.get_connection_info(owner_uri2) is None
    # And asking for a pooled connection returns None.
    assert connection_manager.get_pooled_connection(owner_uri1) is None
    assert connection_manager.get_pooled_connection(owner_uri2) is None


def test_raises_timeout_error_when_pool_maxed_out(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test that a timeout error is raised when the connection pool is maxed out."""
    # Set up the connection manager with a small pool size
    connection_manager = ConnectionManager(
        max_pool_size=2,
        connection_class_factory=mock_connection_class_factory,
    )

    owner_uri_1 = "test_owner_uri_1"
    owner_uri_2 = "test_owner_uri_2"
    details = get_connection_details()
    connection_manager.connect(owner_uri_1, details)
    connection_manager.connect(owner_uri_2, details)

    # Create a connection, put it back with an active transaction

    pooled_connection = connection_manager.get_pooled_connection(owner_uri_1)
    assert pooled_connection is not None
    with pooled_connection as conn:
        # Simulate an active transaction
        mock_connection = conn.connection
        assert isinstance(mock_connection, mock.Mock)
        mock_connection.info.transaction_status = TransactionStatus.INTRANS

    pooled_connection2 = connection_manager.get_pooled_connection(owner_uri_2)
    assert pooled_connection2 is not None
    with pooled_connection2 as _:
        # Attempt to create another connection with the same owner URI
        pooled_connection3 = connection_manager.get_pooled_connection(owner_uri_2)
        assert pooled_connection3 is not None
        with pytest.raises(GetConnectionTimeout) as exec_info, pooled_connection3 as _:
            pass
        assert exec_info.value.pool_size == 2
        assert exec_info.value.active_tx == 1


def test_fetches_expired_azure_token(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test that the connection manager fetches a
    new Azure token when the old one is expired."""
    # Set up the connection manager with a small pool size
    mock_fetch_token = mock.Mock(
        return_value=AzureToken(token="new_token", expiry=int(time.time()) + 3600)
    )
    connection_manager = ConnectionManager(
        fetch_azure_token=mock_fetch_token,
        connection_class_factory=mock_connection_class_factory,
    )

    owner_uri = "test_owner_uri_1"
    details = get_azure_connection_details()

    # Set token to have already expired.
    details.options["azureTokenExpiry"] = int(time.time()) - 100

    connection_manager.connect(owner_uri, details)

    assert mock_fetch_token.called


def test_two_threads_against_expired_token_refreshes_once(
    mock_connection_class_factory: MockConnectionClassFactory,
) -> None:
    """Test that the connection manager fetches a new Azure token
    when the old one is expired."""
    # Set up the connection manager with a small pool size
    mock_fetch_token = mock.Mock(
        return_value=AzureToken(token="new_token", expiry=int(time.time()) + 3600)
    )
    connection_manager = ConnectionManager(
        fetch_azure_token=mock_fetch_token,
        connection_class_factory=mock_connection_class_factory,
    )

    owner_uri_1 = "test_owner_uri_1"
    owner_uri_2 = "test_owner_uri_2"
    details = get_azure_connection_details()

    connection_manager.connect(owner_uri_1, details)
    connection_manager.connect(owner_uri_2, details)

    # Set token to have already expired.
    details.options["azureTokenExpiry"] = int(time.time()) - 100

    # Spin up two threads to get the connection
    # and force the token to be refreshed.
    def thread_func_1() -> None:
        pooled_connection = connection_manager.get_pooled_connection(owner_uri_1)
        assert pooled_connection is not None
        with pooled_connection as _:
            time.sleep(2)

    def thread_func_2() -> None:
        pooled_connection = connection_manager.get_pooled_connection(owner_uri_2)
        assert pooled_connection is not None
        with pooled_connection as _:
            time.sleep(2)

    thread_1 = threading.Thread(target=thread_func_1)
    thread_2 = threading.Thread(target=thread_func_2)
    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()

    # Assert that the token was fetched only once
    assert mock_fetch_token.called
    assert mock_fetch_token.call_count == 1
