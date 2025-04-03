import time
from dataclasses import dataclass
from unittest import mock

import pytest
from psycopg.pq import TransactionStatus

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts.cancellation_request import (
    CANCEL_CONNECT_REQUEST,
    CancelConnectParams,
)
from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.connection.contracts.connect_request import (
    CONNECT_REQUEST,
    ConnectRequestParams,
)
from ossdbtoolsservice.connection.contracts.connection_complete_notification import (
    CONNECTION_COMPLETE_METHOD,
    ConnectionCompleteParams,
)
from ossdbtoolsservice.connection.contracts.disconnect_request import (
    DISCONNECT_REQUEST,
    DisconnectRequestParams,
)
from ossdbtoolsservice.connection.contracts.fetch_azure_token_request import (
    FETCH_AZURE_TOKEN_REQUEST_METHOD,
)
from ossdbtoolsservice.connection.contracts.list_databases import (
    LIST_DATABASES_REQUEST,
    ListDatabasesParams,
    ListDatabasesResponse,
)
from ossdbtoolsservice.connection.core.connection_manager import ConnectionManager
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.query_execution.contracts.execute_request import (
    EXECUTE_STRING_REQUEST_METHOD,
    ExecuteStringParams,
)
from ossdbtoolsservice.query_execution.contracts.message_notification import (
    MESSAGE_NOTIFICATION,
    MessageNotificationParams,
)
from ossdbtoolsservice.query_execution.contracts.result_set_notification import (
    RESULT_SET_COMPLETE_NOTIFICATION,
    ResultSetNotificationParams,
)
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace.contracts.did_change_config_notification import (
    DID_CHANGE_CONFIG_NOTIFICATION,
    Configuration,
    DidChangeConfigurationParams,
)
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService
from tests_v2.connection.conftest import MockConnectionClassFactory
from tests_v2.test_utils.message_server_client_wrapper import (
    MessageServerClientWrapper,
    MockMessageServerClientWrapper,
)
from tests_v2.test_utils.utils import is_debugger_active


@dataclass
class ConnectionServiceTestComponents:
    connection_service: ConnectionService
    connection_manager: ConnectionManager
    workspace_service: WorkspaceService
    connection_class_factory: MockConnectionClassFactory
    mock_server_client_wrapper: MockMessageServerClientWrapper


@pytest.fixture(scope="function")
def connection_service_test_components(
    mock_server_client_wrapper: MockMessageServerClientWrapper,
    mock_connection_class_factory: MockConnectionClassFactory,
) -> ConnectionServiceTestComponents:
    connection_manager = ConnectionManager(
        connection_class_factory=mock_connection_class_factory,
        timeout_override=1000 if is_debugger_active() else None,
    )
    connection_service = ConnectionService(
        connection_manager=connection_manager,
    )
    workspace_service = WorkspaceService()
    mock_server_client_wrapper.add_services(
        {
            constants.CONNECTION_SERVICE_NAME: connection_service,
            constants.WORKSPACE_SERVICE_NAME: workspace_service,
        }
    )

    return ConnectionServiceTestComponents(
        connection_service=connection_service,
        connection_manager=connection_manager,
        workspace_service=workspace_service,
        connection_class_factory=mock_connection_class_factory,
        mock_server_client_wrapper=mock_server_client_wrapper,
    )


def test_connect(connection_service_test_components: ConnectionServiceTestComponents) -> None:
    client = connection_service_test_components.mock_server_client_wrapper
    connection_service = connection_service_test_components.connection_service

    # Create a connection
    connection_uri = "testuri"
    connection_details = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    response = client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    assert response.result is True

    notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
    params = notfication.get_params(ConnectionCompleteParams)

    assert params.owner_uri == connection_uri
    assert params.error_message is None
    assert params.connection_id is not None
    assert params.server_info is not None
    assert params.connection_summary is not None

    # Check that we can get the connection
    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is not None


def test_connection_from_multiple_uris_create_correct_pools(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that multiple connection requests create the correct pools"
    only create one connection pool."""
    client = connection_service_test_components.mock_server_client_wrapper
    connection_service = connection_service_test_components.connection_service
    connection_manager = connection_service_test_components.connection_manager

    connection_details_1 = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    connection_details_2 = ConnectionDetails(
        {"host": "someserver", "port": 5432, "user": "test_user"}
    )
    connection_uri_1 = "testuri_1"  # Connected to localhost
    connection_uri_2 = "testuri_2"  # Connected to localhost
    connection_uri_3 = "testuri_3"  # Connected to someserver

    for uri in [connection_uri_1, connection_uri_2]:
        response = client.send_client_request(
            CONNECT_REQUEST.method,
            ConnectRequestParams(
                owner_uri=uri,
                connection=connection_details_1,
            ),
        )
        assert response.result is True

    response = client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri_3,
            connection=connection_details_2,
        ),
    )
    assert response.result is True

    for _ in range(3):
        notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
        params = notfication.get_params(ConnectionCompleteParams)

        assert params.owner_uri in [connection_uri_1, connection_uri_2, connection_uri_3]
        assert params.error_message is None
        connection_summary = params.connection_summary
        assert connection_summary is not None
        if params.owner_uri == connection_uri_3:
            assert connection_summary.server_name == "someserver"
        else:
            assert connection_summary.server_name == "localhost"

    pooled_connection_1 = connection_service.get_pooled_connection(connection_uri_1)
    pooled_connection_2 = connection_service.get_pooled_connection(connection_uri_2)
    pooled_connection_3 = connection_service.get_pooled_connection(connection_uri_3)
    assert pooled_connection_1 is not None
    assert pooled_connection_2 is not None
    assert pooled_connection_3 is not None

    # Check that the connection pools are correct
    pool_name_1 = str(connection_details_1.to_hash())
    pool_name_2 = str(connection_details_2.to_hash())
    stats = connection_manager.get_pool_stats()
    assert len(stats) == 2
    assert pool_name_1 in stats
    assert pool_name_2 in stats
    assert stats[pool_name_1]["pool_size"] == 1
    assert stats[pool_name_2]["pool_size"] == 1

    # Check that the pools produce connections as expected

    with (
        pooled_connection_1 as conn1,
        pooled_connection_2 as _,
        pooled_connection_3 as _,
    ):
        stats = connection_manager.get_pool_stats()
        assert stats[pool_name_1]["pool_size"] == 2
        assert stats[pool_name_2]["pool_size"] == 1

        # Set one of the connections to localhost to be in a transaction,
        # which will keep it from being returned to the pool.
        assert isinstance(conn1._conn, mock.Mock)
        conn1._conn.info.transaction_status = TransactionStatus.INTRANS

    # Now open two connections to owner_uri_2. Since owner_uri_1 is holding
    # a connection in transaction, the pool should grow to 3.
    pooled_connection_2a = connection_service.get_pooled_connection(connection_uri_2)
    assert pooled_connection_2a is not None
    pooled_connection_2b = connection_service.get_pooled_connection(connection_uri_2)
    assert pooled_connection_2b is not None
    with pooled_connection_2a as _, pooled_connection_2b as _:
        stats = connection_manager.get_pool_stats()
        assert stats[pool_name_1]["pool_size"] == 3


def test_connection_pool_uses_configuration(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that multiple connection requests create the correct pools"
    only create one connection pool."""
    client = connection_service_test_components.mock_server_client_wrapper
    workspace_service = connection_service_test_components.workspace_service
    connection_manager = connection_service_test_components.connection_manager

    config = Configuration()
    config.pgsql.max_connections = 20

    client.send_client_notification(
        method=DID_CHANGE_CONFIG_NOTIFICATION.method,
        params=DidChangeConfigurationParams(
            configuration=config,
        ),
    )

    time.sleep(0.1)  # Give the notification time to be processed

    assert workspace_service.configuration.pgsql.max_connections == 20

    connection_details = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    connection_uri = "testuri_1"

    response = client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    assert response.result is True

    notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
    params = notfication.get_params(ConnectionCompleteParams)
    assert params.owner_uri == connection_uri

    # Check that the connection pools are correct
    pool_name = str(connection_details.to_hash())
    stats = connection_manager.get_pool_stats()
    assert pool_name in stats
    assert stats[pool_name]["pool_max"] == 20


def test_fetches_stale_azure_token(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that the azure token is fetched when it is stale."""
    _clock_rolled_forward = False
    tick = 0

    def time_nows() -> int:
        nonlocal _clock_rolled_forward, tick
        if _clock_rolled_forward:
            tick += 1
            return 10000 + tick
        tick += 1
        return tick

    with mock.patch("time.time", side_effect=time_nows):
        client = connection_service_test_components.mock_server_client_wrapper
        connection_service = connection_service_test_components.connection_service

        client.setup_client_response(
            FETCH_AZURE_TOKEN_REQUEST_METHOD,
            JSONRPCMessage.create_response(
                msg_id=1,
                result={
                    "token": "test_token",
                    "expiry": 20000,
                },
            ),
        )

        # Create a connection
        connection_uri = "testuri"
        connection_details = ConnectionDetails(
            {
                "host": "localhost",
                "port": 5432,
                "user": "test_user",
                "azureAccountId": "test_account_id",
                "azureTenantId": "test_tenant_id",
                "azureAccountToken": "test_token",
                "azureTokenExpiry": 10000,
            }
        )
        response = client.send_client_request(
            CONNECT_REQUEST.method,
            ConnectRequestParams(
                owner_uri=connection_uri,
                connection=connection_details,
            ),
        )
        assert response.result is True

        notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
        params = notfication.get_params(ConnectionCompleteParams)

        assert params.owner_uri == connection_uri
        assert params.error_message is None

        # Create connection should succeed
        pooled_connection = connection_service.get_pooled_connection(connection_uri)
        assert pooled_connection is not None
        with pooled_connection as conn:
            assert conn.transaction_is_idle

        # Fetch token shouldn't have been called yet
        assert client.get_server_message_count(FETCH_AZURE_TOKEN_REQUEST_METHOD) == 0

        # Fast forward time
        _clock_rolled_forward = True

        # Grab two connections, so that the pool needs to grow.
        pooled_connection_1 = connection_service.get_pooled_connection(connection_uri)
        assert pooled_connection_1 is not None
        pooled_connection_2 = connection_service.get_pooled_connection(connection_uri)
        assert pooled_connection_2 is not None
        with pooled_connection_1 as conn_1, pooled_connection_2 as conn_2:
            assert conn_1.transaction_is_idle
            assert conn_2.transaction_is_idle

        # Check that the token was fetched
        assert client.get_server_message_count(FETCH_AZURE_TOKEN_REQUEST_METHOD) == 1


def test_disconnect(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that disconnecting a connection works as expected."""
    client = connection_service_test_components.mock_server_client_wrapper
    connection_service = connection_service_test_components.connection_service

    # Create a connection
    connection_uri = "testuri"
    connection_details = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    response = client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    assert response.result is True

    notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
    params = notfication.get_params(ConnectionCompleteParams)

    assert params.owner_uri == connection_uri
    assert params.error_message is None

    # Disconnect the connection
    response = client.send_client_request(
        DISCONNECT_REQUEST.method,
        DisconnectRequestParams(owner_uri=connection_uri),
    )
    assert response.result is True

    # Check that the connection is closed
    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is None
    # Check that the connection pool is closed
    pool_name = str(connection_details.to_hash())
    stats = connection_service_test_components.connection_manager.get_pool_stats()
    assert len(stats) == 0
    assert pool_name not in stats
    # Check that the connection is closed
    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is None


def test_cancel_connect(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that canceling a connection works as expected."""
    client = connection_service_test_components.mock_server_client_wrapper
    connection_service = connection_service_test_components.connection_service

    # Create a connection
    connection_uri = "testuri"
    connection_details = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    response = client.send_client_request(
        CANCEL_CONNECT_REQUEST.method,
        CancelConnectParams(owner_uri=connection_uri),
    )
    assert response.result is True

    # Check that the connection is closed
    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is None
    # Check that the connection pool is closed
    pool_name = str(connection_details.to_hash())
    stats = connection_service_test_components.connection_manager.get_pool_stats()
    assert len(stats) == 0
    assert pool_name not in stats
    # Check that the connection is closed
    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is None


def test_list_databases(
    connection_service_test_components: ConnectionServiceTestComponents,
) -> None:
    """Test that listing databases works as expected."""
    client = connection_service_test_components.mock_server_client_wrapper
    connection_service = connection_service_test_components.connection_service

    # Create a connection
    connection_uri = "testuri"
    connection_details = ConnectionDetails(
        {"host": "localhost", "port": 5432, "user": "test_user"}
    )
    response = client.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    assert response.result is True

    notfication = client.wait_for_notification(CONNECTION_COMPLETE_METHOD)
    params = notfication.get_params(ConnectionCompleteParams)

    assert params.owner_uri == connection_uri
    assert params.error_message is None

    pooled_connection = connection_service.get_pooled_connection(connection_uri)
    assert pooled_connection is not None
    with pooled_connection as conn:
        pg_conn = conn._conn
        assert isinstance(pg_conn, mock.Mock)
        # Mock the list databases response
        pg_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            ("db1",),
            ("db2",),
            ("db3",),
        ]

    # List databases
    response = client.send_client_request(
        LIST_DATABASES_REQUEST.method,
        ListDatabasesParams(owner_uri=connection_uri),
    )
    result = response.get_result(ListDatabasesResponse)
    assert result.database_names == ["db1", "db2", "db3"]


# ---------- Tests using actual connections ----------


def test_connection_in_transaction_requires_rollback(
    server_client_wrapper: MessageServerClientWrapper,
    connection_string: str,
) -> None:
    """Test that a connection in transaction requires rollback
    before being returned to the pool."""

    # Create a connection
    connection_uri = "testuri"
    connection_details = ConnectionDetails.from_connection_string(
        connection_string,
    )
    response = server_client_wrapper.send_client_request(
        CONNECT_REQUEST.method,
        ConnectRequestParams(
            owner_uri=connection_uri,
            connection=connection_details,
        ),
    )
    assert response.result is True

    connection_notification = server_client_wrapper.wait_for_notification(
        CONNECTION_COMPLETE_METHOD, pop_message=True
    )
    cn_params = connection_notification.get_params(ConnectionCompleteParams)

    assert cn_params.owner_uri == connection_uri
    assert cn_params.error_message is None

    # Begin a transaction
    server_client_wrapper.send_client_request(
        EXECUTE_STRING_REQUEST_METHOD,
        ExecuteStringParams(
            owner_uri=connection_uri,
            query="BEGIN",  # Start a transaction
        ),
    )

    query_1_complete_notification = server_client_wrapper.wait_for_notification(
        RESULT_SET_COMPLETE_NOTIFICATION, pop_message=True
    )
    query_1_params = query_1_complete_notification.get_params(ResultSetNotificationParams)
    assert query_1_params.owner_uri == connection_uri
    assert query_1_params.result_set_summary is None

    # Execute statement that will fail.
    server_client_wrapper.clear_notifications()
    response = server_client_wrapper.send_client_request(
        EXECUTE_STRING_REQUEST_METHOD,
        ExecuteStringParams(
            owner_uri=connection_uri,
            query="SELECT * FROM table_no_exist",
        ),
    )

    query_2_message_notifications = server_client_wrapper.wait_for_notification(
        MESSAGE_NOTIFICATION, pop_message=True
    )
    query_2_params = query_2_message_notifications.get_params(MessageNotificationParams)
    assert query_2_params.message.is_error is True

    # Try to execute a statement that is not a rollback.
    server_client_wrapper.clear_notifications()
    response = server_client_wrapper.send_client_request(
        EXECUTE_STRING_REQUEST_METHOD,
        ExecuteStringParams(
            owner_uri=connection_uri,
            query="SELECT 1",
        ),
    )

    query_3_message_notifications = server_client_wrapper.wait_for_notification(
        MESSAGE_NOTIFICATION, pop_message=True
    )
    query_3_params = query_3_message_notifications.get_params(MessageNotificationParams)
    assert query_3_params.message.is_error is True
    assert "ROLLBACK" in query_3_params.message.message

    # Rollback the transaction
    server_client_wrapper.clear_notifications()
    response = server_client_wrapper.send_client_request(
        EXECUTE_STRING_REQUEST_METHOD,
        ExecuteStringParams(
            owner_uri=connection_uri,
            query="ROLLBACK",
        ),
    )

    query_4_complete_notification = server_client_wrapper.wait_for_notification(
        RESULT_SET_COMPLETE_NOTIFICATION, pop_message=True
    )
    query_4_params = query_4_complete_notification.get_params(ResultSetNotificationParams)
    assert query_4_params.owner_uri == connection_uri
    assert query_4_params.result_set_summary is None
