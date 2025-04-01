from collections.abc import Generator
from unittest import mock

import pytest
from psycopg.conninfo import conninfo_to_dict
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)

from evaluations.chat_service_wrapper import ChatServiceWrapper
from evaluations.settings import EvaluationSettings
from ossdbtoolsservice.chat.chat_service import ChatService
from ossdbtoolsservice.connection import (
    ConnectionService,
    ServerConnection,
)
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from tests_v2.test_utils.message_server_client_wrapper import MockMessageServerClientWrapper
from tests_v2.test_utils.queue_message_server import QueueRPCMessageServer

# def pytest_addoption(parser: pytest.Parser) -> None:
#     # TODO: How to get VS Code pytest settings to not pass --playback for evaluations?
#     parser.addoption(
#         "--playback",
#         action="store_true",
#         default=False,
#         help="Not used.",
#     )


@pytest.fixture(scope="session")
def eval_settings() -> EvaluationSettings:
    return EvaluationSettings(_env_file=".env")  # pyright: ignore


@pytest.fixture
def async_runner() -> AsyncRunner:
    """Create a fixture for AsyncRunner.

    All async calls must be run in the same thread, so use this
    fixture to execute async calls.
    """
    return AsyncRunner()


@pytest.fixture(scope="function")
def mock_server_client_wrapper(
    eval_settings: EvaluationSettings,
    async_runner: AsyncRunner,
) -> Generator[MockMessageServerClientWrapper, None, None]:
    """Mock server client wrapper that has the necessary services registered or mocked."""
    # Create a connection service that returns a ServerConnection to our database
    connection_info = conninfo_to_dict(eval_settings.connection_string)
    server_connection = ServerConnection(
        # ConnDict -> dict[str, str | int]
        conn_params=connection_info  # type: ignore
    )
    connection_service_mock = mock.MagicMock(spec=ConnectionService)
    connection_service_mock.get_connection.return_value = server_connection

    # Setup Azure OpenAI completions
    chat_completion = AzureChatCompletion(
        api_key=eval_settings.azure_openai_api_key,
        deployment_name=eval_settings.azure_openai_chat_deployment_name,
        endpoint=eval_settings.azure_openai_endpoint,
        api_version=eval_settings.azure_openai_api_version,
    )
    prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        max_tokens=10000,
        temperature=0.7,
        top_p=0.8,
    )

    # Create chat service
    chat_service = ChatService(
        chat_completion=chat_completion, execution_settings=prompt_execution_settings
    )

    # Setup client wrapper
    server = QueueRPCMessageServer(async_runner=async_runner)
    with server:
        server.add_services(
            {
                "chat": chat_service,
                "connection": connection_service_mock,
            }
        )
        wrapper = MockMessageServerClientWrapper(server)
        with wrapper:
            yield wrapper


@pytest.fixture(scope="function")
def chat_service_wrapper(
    mock_server_client_wrapper: MockMessageServerClientWrapper,
) -> ChatServiceWrapper:
    """Chat service wrapper fixture."""
    return ChatServiceWrapper(mock_server_client_wrapper)
