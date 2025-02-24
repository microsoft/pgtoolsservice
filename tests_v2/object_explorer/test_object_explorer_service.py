from unittest import mock

import pytest

from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.connection.contracts.common import ConnectionDetails, ConnectionType
from ossdbtoolsservice.connection.contracts.connection_complete_notification import (
    ConnectionCompleteParams,
)
from ossdbtoolsservice.driver.types.driver import ServerConnection
from ossdbtoolsservice.object_explorer.contracts.create_session_request import (
    CREATE_SESSION_REQUEST,
    CreateSessionResponse,
)
from ossdbtoolsservice.object_explorer.contracts.get_session_id_request import (
    GET_SESSION_ID_REQUEST,
    GetSessionIdResponse,
)
from ossdbtoolsservice.object_explorer.contracts.session_created_notification import (
    SESSION_CREATED_METHOD,
    SessionCreatedParameters,
)
from ossdbtoolsservice.object_explorer.object_explorer_service import ObjectExplorerService
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.workspace.contracts.did_change_config_notification import Configuration
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService
from tests_v2.test_utils.mock_message_server import MockMessageServer


@pytest.mark.parametrize(
    "init_success",
    [
        (True),
        (False),
    ],
)
def test_create_session_request(
    mock_message_server: MockMessageServer, init_success: bool
) -> None:
    """Test sending a request to the message server and receiving a response."""

    # The create session request will create a session and return it to the client.
    # On another thread, it will initialize that session.
    # The status of the session initialization is sent in a follow up notification
    # that indicates success or failure.

    expected_session_id = "objectexplorer://test_user@localhost:5432:postgres/"

    # Creating a session fetches the configuration
    workspace_service_mock = mock.MagicMock(spec=WorkspaceService)
    workspace_service_mock.configuration = Configuration()

    # Creating a session will establish a connection
    connection_service_mock = mock.MagicMock(spec=ConnectionService)

    connection_complete_params = ConnectionCompleteParams()
    if not init_success:
        connection_complete_params.error_message = "Connection failed"
    else:
        connection_complete_params.owner_uri = expected_session_id
        connection_complete_params.connection_summary = None
        connection_complete_params.type = ConnectionType.OBJECT_EXLPORER

        # Mock the connection.
        server_connection_mock = mock.MagicMock(spec=ServerConnection)
        server_connection_mock.host_name = "localhost"
        server_connection_mock.port = 5432
        server_connection_mock.user_name = "test_user"
        server_connection_mock.database_name = "postgres"
        connection_service_mock.get_connection.return_value = server_connection_mock

    connection_service_mock.connect.return_value = connection_complete_params

    mock_message_server.add_services(
        {
            constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
            constants.WORKSPACE_SERVICE_NAME: workspace_service_mock,
            constants.CONNECTION_SERVICE_NAME: connection_service_mock,
        }
    )

    req_params = ConnectionDetails.from_data(
        {
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
        }
    )

    expected_result = CreateSessionResponse(expected_session_id)

    response = mock_message_server.send_client_request(
        CREATE_SESSION_REQUEST.method, req_params
    )

    assert isinstance(response, CreateSessionResponse)
    assert response.session_id == expected_result.session_id

    session_created = mock_message_server.wait_for_notification(SESSION_CREATED_METHOD)
    assert isinstance(session_created, SessionCreatedParameters)

    assert session_created.session_id == expected_result.session_id
    assert session_created.success == init_success, (
        f"Error initializing session: {session_created.error_message}"
    )


def test_get_session_id_request(
    mock_message_server: MockMessageServer,
) -> None:
    # Test sending a request for a session ID from a ConnectionDetails object
    # and receiving a response.
    expected_session_id = "objectexplorer://test_user@localhost:5432:postgres/"

    # Creating a session fetches the configuration
    workspace_service_mock = mock.MagicMock(spec=WorkspaceService)
    workspace_service_mock.configuration = Configuration()
    mock_message_server.add_services(
        {
            constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
            constants.WORKSPACE_SERVICE_NAME: workspace_service_mock,
        }
    )
    req_params = ConnectionDetails.from_data(
        {
            "host": "localhost",
            "port": 5432,
            "user": "test_user",
            "dbname": "postgres",
        }
    )
    response = mock_message_server.send_client_request(
        GET_SESSION_ID_REQUEST.method, req_params
    )
    assert isinstance(response, GetSessionIdResponse)
    assert response.session_id == expected_session_id
